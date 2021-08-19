"""
This script merges the sidewalk line geometries and `mcpc_srts_projects` layers
into a single topologically-sound layer. It requires splitting segments
within each layer wherever there is an intersection between the two layers.
"""
import pandas as pd
from pg_data_etl import Database
from pg_data_etl.database.actions.query.simple import query_as_list_of_lists

from network_routing import pg_db_connection
from network_routing.database.setup.make_nodes import generate_nodes


def add_segmentation_to_new_lines(
    db: Database,
    base_network_name: str = "pedestriannetwork_lines",
    new_line_tablename: str = "mcpc_srts_projects",
    groupid_colname: str = "groupid",
) -> list:
    """ Split the trail layer wherever it intersects a sidewalk """
    print("#" * 55)
    print("Adding segmentation to new lines")

    # Split the new lines wherever they intersect a sidwalk
    # --------------------------------------------------

    newline_split = f"""
        select
            {groupid_colname},
            (st_dump(
                st_split(
                    t1.geom,
                    (select st_collect(geom)
                    from {base_network_name} p1
                    where st_intersects(t1.geom, p1.geom)
                    )
                )
            )).geom
        from {new_line_tablename} t1
    """

    split_table = f"{new_line_tablename}_splits"

    db.gis_make_geotable_from_query(newline_split, split_table, geom_type="LINESTRING", epsg=26918)

    # Merge the split trails with any trails that didn't get split
    # ------------------------------------------------------------

    newline_merge = f"""
        select
            'newline - raw' as src,
            {groupid_colname} as groupid,
            geom
        from {new_line_tablename}
        where
            not st_within(geom, (select st_buffer(st_collect(geom), 1.5) from {split_table} ts2) )

        union

        select
            'newline - split' as src,
            {groupid_colname} as groupid,
            geom
        from {split_table}
    """
    merged_table = f"{new_line_tablename}_merged"
    db.gis_make_geotable_from_query(newline_merge, merged_table, geom_type="LINESTRING", epsg=26918)

    return [split_table, merged_table]


def add_segmentation_to_sidewalks(
    db: Database,
    base_network_name: str = "pedestriannetwork_lines",
    new_line_tablename: str = "mcpc_srts_projects",
    groupid_colname: str = "groupid",
) -> list:
    print("#" * 55)
    print("Adding segmentation to sidewalks lines")

    # Split the sidewalks wherever they intersect a trail
    # ---------------------------------------------------

    sidewalk_split_query = f"""
        select
            globalid,
            (st_dump(
                st_split(
                    s.geom,
                    (select st_collect(geom)
                     from {new_line_tablename} t
                     where st_intersects(s.geom, t.geom)
                    )
                )
            )).geom
        from {base_network_name} s
    """
    sidewalk_splits = f"{new_line_tablename}_sidewalk_splits"
    db.gis_make_geotable_from_query(
        sidewalk_split_query, sidewalk_splits, geom_type="LINESTRING", epsg=26918
    )

    # Merge the split sidewalks with any sidewalks that didn't get split
    # ------------------------------------------------------------------

    sidewalk_merge_query = f"""
        select
            'sidewalk - raw' as src,
            geom
        from {base_network_name}
        where
            not st_within(geom, (select st_buffer(st_collect(geom), 0.5) from {sidewalk_splits}) )

        union

        select
            'sidewalk - split' as src,
            geom
        from {sidewalk_splits}
    """
    sidewalk_merge = f"{new_line_tablename}_sidewalk_merged"
    db.gis_make_geotable_from_query(
        sidewalk_merge_query, sidewalk_merge, geom_type="LINESTRING", epsg=26918
    )

    return [sidewalk_splits, sidewalk_merge]


def merge_sidewalks_and_newlines(
    db: Database,
    existing_lines: str = "mcpc_srts_projects_sidewalk_merged",
    new_lines: str = "mcpc_srts_projects_merged",
    output_tablename: str = "mcpc_srts_projects_with_existing_network",
):
    print("#" * 55)
    print("Merging sidewalks and new lines")

    # Merge both split tables together
    query = f"""
        SELECT src, groupid, geom FROM {new_lines}
        UNION
        SELECT src, 'EXISTING NETWORK' as groupid, geom FROM {existing_lines}
    """
    db.gis_make_geotable_from_query(query, output_tablename, geom_type="LINESTRING", epsg=26918)

    # Generate the nodes necessary for subsequent analysis
    generate_nodes(
        db,
        output_tablename,
        geotable_kwargs={
            "new_table_name": f"nodes_for_{output_tablename}",
            "uid_col": "node_id",
            "geom_type": "Point",
            "epsg": 26918,
        },
    )


def draw_missing_links_to_new_lines(
    db: Database,
    edge_table: str = "mcpc_srts_projects_with_existing_network",
    new_line_tablename: str = "mcpc_srts_projects_merged",
) -> list:
    print("#" * 55)
    print("Drawing missing links and regenerating network data")

    # Iterate over every line
    # If the start or endpoint does not intersect the base network,
    # then we want to draw a line to the nearest base network node

    line_ids = db.query_as_list_of_lists(
        f"""
        select uid, groupid from {new_line_tablename}
    """
    )
    all_results = []
    for uid, groupid in line_ids:
        print(uid, groupid)
        query = f"""
            with point as (
                select st_startpoint(geom) as geom
                from {new_line_tablename}
                where uid = {uid}
            )
            select 
                '{groupid}' as groupid,
                st_makeline(n.geom, p.geom) as geom
            from
                nodes_for_{edge_table} n,
                point p
            where
                st_dwithin(n.geom, p.geom, 10)
            and not
                st_intersects(n.geom, p.geom)
            order by
                st_distance(n.geom, p.geom) asc
            limit 1
        """

        start_point_connector = db.gdf(query)

        all_results.append(start_point_connector)

        end_point_connector = db.gdf(query.replace("st_startpoint", "st_endpoint"))

        all_results.append(end_point_connector)

        print("------")

    combined_gdf = pd.concat(all_results)

    temp_line_connectors = "temp_line_connectors"

    db.import_geodataframe(combined_gdf, temp_line_connectors, gpd_kwargs={"if_exists": "replace"})

    # Update (/overwrite!) the edge network to include these new connectors
    query = f"""
    	select src, groupid, geom
        from {edge_table}
        union
        select 
            'from postgis + python' as src, 
            groupid,
            geom
        from 
            {temp_line_connectors}
    """

    gdf = db.gdf(query)

    db.import_geodataframe(gdf, edge_table, gpd_kwargs={"if_exists": "replace"})

    return [temp_line_connectors]


def cleanup_temp_tables(db: Database, list_of_tables_to_drop: list):
    """ Delete the intermediate tables to keep the DB clean """
    print("#" * 55)
    print("Removing interim tables")

    for tbl in list_of_tables_to_drop:
        db.execute(f"DROP TABLE {tbl};")


def merge_topologies(db: Database):

    tables_to_cleanup = []

    tables_to_cleanup += add_segmentation_to_new_lines(db)

    tables_to_cleanup += add_segmentation_to_sidewalks(db)

    merge_sidewalks_and_newlines(db)

    tables_to_cleanup += draw_missing_links_to_new_lines(db)

    cleanup_temp_tables(db, tables_to_cleanup)


if __name__ == "__main__":
    db = pg_db_connection()

    merge_topologies(db)

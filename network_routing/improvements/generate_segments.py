"""
generate_segments.py
--------------------

For every OpenStreetMap segment with zero parallel sidewalks,
generate two new 'improvement concept' geometries, one for each
side of the street centerline.

"""
import pandas as pd
from tqdm import tqdm
import sqlalchemy
from geoalchemy2 import Geometry, WKTElement

import warnings

from pg_data_etl import Database
from network_routing import pg_db_connection

warnings.filterwarnings("ignore")


def generate_missing_network(
    db: Database,
    output_table: str = "improvements.all_possible_geoms",
    county_name: str = "Montgomery",
) -> None:
    """
    Find OSM centerlines that don't have sidewalks on
    both sides, and draw a parallel on each side.

    This generates a table named:
        improvements.all_possible_projects

    NOTE!
    This code builds upon the output from:
        > gaps classify-osm-sw-coverage
    """

    schema, tablename = output_table.split(".")

    output_table += "_" + county_name.lower()

    db.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")

    id_query = f"""
        with regional_bounds as (
            select geom
            from public.regional_counties
            where co_name = '{county_name}'
        )
        select s.uid
        from public.osm_edges_drive s, regional_bounds rb
        where
            s.sidewalk < (st_length(s.geom) * 2)
        and s.analyze_sw = 1
        and hwy_tag != 'motorway'
        and st_intersects(s.geom, rb.geom)
    """

    # if output_table in db.tables(schema=schema):
    #     already_processed_uids_query = f"""
    #         select distinct osm_src_uid from {output_table};
    #     """
    #     ids_to_skip = db.query_as_list_of_singletons(already_processed_uids_query)
    #     ids_sql_format = str(tuple(ids_to_skip))

    #     id_query += f"""
    #         and uid not in {ids_sql_format}
    #     """

    uids_to_analyze = db.query_as_list_of_singletons(id_query)

    for uid in tqdm(uids_to_analyze, total=len(uids_to_analyze)):

        query = f"""
            with segment as (
                select
                    uid,
                    geom
                from public.osm_edges_drive
                where uid = {uid}
            ),
            left_side as (
                select
                    uid as osm_src_uid,
                    st_offsetcurve(geom, 10) as geom,
                    'left' as side
                from segment
            ),
            right_side as (
                select
                    uid as osm_src_uid,
                    st_offsetcurve(geom, -10) as geom,
                    'right' as side
                from segment
            )
            select * from left_side
            union
            select * from right_side
        """

        gdf = db.gdf(query)

        db.import_geodataframe(
            gdf,
            output_table,
            explode=True,
            gpd_kwargs={"if_exists": "append"},
        )


if __name__ == "__main__":

    db = pg_db_connection()
    generate_missing_network(db)

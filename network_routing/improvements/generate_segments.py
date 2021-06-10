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


def generate_missing_network(db: Database) -> None:
    """
    Find OSM centerlines that don't have sidewalks on
    both sides, and draw a parallel on each side.

    This generates a table named:
        data_viz.all_possible_improvements

    NOTE!
    This code builds upon the output from:
        > gaps classify-osm-sw-coverage
    """

    id_query = """
        with regional_bounds as (
            select st_union(geom) as geom
            from public.regional_counties
        )
        select s.uid
        from public.osm_edges_drive s, regional_bounds rb
        where
            s.sidewalk < (st_length(s.geom) * 2)
        and s.analyze_sw = 1
        and st_intersects(s.geom, rb.geom)
    """

    if "data_viz.all_possible_improvements" in db.tables(schema="data_viz"):
        already_processed_uids_query = """
            select distinct osm_src_uid from data_viz.all_possible_improvements;
        """
        ids_to_skip = db.query_as_list_of_singletons(already_processed_uids_query)
        ids_sql_format = str(tuple(ids_to_skip))

        id_query += f"""
            and uid not in {ids_sql_format}
        """

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

        # Ensure it's exploded to singlepart
        gdf = gdf.explode()
        gdf["explode"] = gdf.index
        gdf.reset_index(inplace=True)

        gdf["geom"] = gdf["geom"].apply(lambda x: WKTElement(x.wkt, srid=26918))

        engine = sqlalchemy.create_engine(db.uri)
        gdf.to_sql(
            "all_possible_improvements",
            engine,
            schema="data_viz",
            dtype={"geom": Geometry("LINESTRING", srid=26918)},
            if_exists="append",
        )
        engine.dispose()

        db.table_add_uid_column("data_viz.all_possible_improvements")
        db.gis_table_add_spatial_index("data_viz.all_possible_improvements")


if __name__ == "__main__":

    db = pg_db_connection()
    generate_missing_network(db)

"""
generate_segments.py
--------------------

For every OpenStreetMap segment with zero parallel sidewalks,
generate two new 'improvement concept' geometries, one for each
side of the street centerline.

"""
import pandas as pd
from tqdm import tqdm
from postgis_helpers.PgSQL import PostgreSQL

from network_routing import db_connection


def generate_missing_network(db: PostgreSQL) -> None:
    """
    Find OSM centerlines that have NO sidewalk (sidewalk = 0), and
    draw a parallel on each side.

    This generates a table named:
        data_viz.improvement_concepts

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
            s.sidewalk = 0
        and s.analyze_sw = 1
        and st_intersects(s.geom, rb.geom)
    """
    segments_that_need_both_sidewalks = db.query_as_list(id_query)

    all_gdfs = []
    counter = 0

    for segment_uid in tqdm(
        segments_that_need_both_sidewalks, total=len(segments_that_need_both_sidewalks)
    ):
        uid = segment_uid[0]
        counter += 1

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

        gdf = db.query_as_geo_df(query)

        all_gdfs.append(gdf)

    # Save the full table at the end of the run
    db.import_geodataframe(pd.concat(all_gdfs), "improvement_concepts_final", schema="data_viz")


if __name__ == "__main__":

    db = db_connection()
    generate_missing_network(db)

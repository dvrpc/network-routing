"""
generate_segments.py
--------------------

For every OpenStreetMap segment with zero parallel sidewalks,
generate two new 'improvement concept' geometries, one for each
side of the street centerline.

"""
import click
import pandas as pd
from tqdm import tqdm

import warnings

from pg_data_etl import Database
from network_routing import pg_db_connection

warnings.filterwarnings("ignore")


@click.command()
def draw_missing_network_links():
    """Create a full sidewalk network on streets lacking sidewalks on both sides"""

    db = pg_db_connection()

    generate_missing_network(db)


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
        from 
            osm_edges_drive_no_motorway s, 
            regional_bounds rb
        where
            s.sidewalk < (st_length(s.geom) * 2)
        and s.analyze_sw = 1
        and highway not like '%%motorway%%'
        and st_intersects(s.geom, rb.geom)
    """

    uids_to_analyze = db.query_as_list_of_singletons(id_query)

    counter = 0
    first_two_gdfs = []

    for uid in tqdm(uids_to_analyze, total=len(uids_to_analyze)):

        counter += 1

        query = f"""
            with segment as (
                select
                    uid,
                    geom
                from public.osm_edges_drive_no_motorway
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

        if counter <= 2:
            first_two_gdfs.append(gdf)

        if counter == 2:
            merged_gdf = pd.concat(first_two_gdfs)

        elif counter > 2:
            merged_gdf = pd.concat([merged_gdf, gdf])

    print("Writing to shapefile")
    shp_path = f"./shp/{output_table.replace('.', '_')}.shp"
    merged_gdf.to_file(shp_path)

    print("Writing to postgis")
    db.import_gis(
        filepath=shp_path,
        sql_tablename=output_table,
        explode=True,
        gpd_kwargs={"if_exists": "replace"},
    )


if __name__ == "__main__":

    db = pg_db_connection()
    generate_missing_network(db)

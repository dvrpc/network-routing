import click
import pandas as pd
from tqdm import tqdm
from pg_data_etl import Database

from network_routing import pg_db_connection

# This silences the geopandas warning: "UserWarning: Geometry column does not contain geometry."
import warnings

warnings.filterwarnings("ignore")


@click.command()
def feature_engineering():
    """
    Erase & split the drawn lines to remove existing feature and make a topologically connected network
    """

    db = pg_db_connection()

    erase_features(db)
    split_features(db)


def erase_features(db: Database, tablename: str = "improvements.all_possible_geoms") -> None:
    """
    Iterate over all features in the 'all_possible_improvements' table.

    Erase any parts of the geometry within a 10 meter buffer of nearby sidewalks.
    Keep whatever remains and write to a new table named: 'data_viz.cleaned_improvements'
    """

    # counties = db.query_as_list_of_singletons("select distinct co_name from regional_counties")
    counties = [
        "Gloucester",
        "Camden",
        "Burlington",
        "Mercer",
        # "Montgomery",
        # "Bucks",
        # "Chester",
        # "Delaware",
        # "Philadelphia",
    ]

    # Operate one county at a time, writing/appending results before moving to the next one
    for county_name in counties:

        src_table = tablename + "_" + county_name.lower()

        print(f"Processing county: {county_name}")

        uids = db.query_as_list_of_singletons(
            f"""
            select uid from {src_table}
            where st_within(
                st_centroid(geom),
                (select geom from regional_counties where co_name = '{county_name}')
            )
        """
        )

        # Iterate over every feature that was previously drawn in this county

        counter = 0
        first_two_gdfs = []

        for uid in tqdm(uids, total=len(uids)):

            q = f"""
            with seg as (
                -- filter new segments to a single new geometry

                select geom
                from {src_table}
                where uid = {uid}
            ),
            sw_buff as (
                -- select sidewalks within 10meters
                -- and turn those features into a single buffer poly

                select st_buffer(st_collect(pl.geom), 10) as geom
                from pedestriannetwork_lines pl, seg
                where st_dwithin(pl.geom, seg.geom, 10)
            ),
            diff as (
                -- find the line geometry that does not intersect the poly

                select st_difference(s.geom, b.geom) as geom
                from seg s, sw_buff b
            )
            select geom
            from diff
            """

            # Get the query output
            gdf = db.gdf(q)

            # Parse the result of the output and act accordingly...

            if gdf.iloc[0].geom is None:

                # a None result means there is zero overlap and we want to grab the whole source feature

                gdf = db.gdf(
                    f"""
                    select geom from {src_table} where uid = {uid}
                """
                )
                gdf["src_uid"] = uid

            elif gdf.iloc[0].geom.is_empty:
                # An empty result means the entire source geometry was erased (i.e. this sw already exists fully)
                # as a result, we will skip all of the subsequent lines of code inside this 'for' loop
                continue
            else:
                # Something remained after the erase, so let's keep what we got
                gdf["src_uid"] = uid

            # Handle the combination of this result with prior results
            # First two runs through get put into a list
            counter += 1

            if counter <= 2:
                first_two_gdfs.append(gdf)

            # On the second iteration, merge the first two results
            if counter == 2:
                merged_gdf = pd.concat(first_two_gdfs)

            # Every subsequent iteration, merge it to the larger result set
            elif counter > 2:
                merged_gdf = pd.concat([merged_gdf, gdf])

        print("Writing shapefile")
        shp_path = f"./{county_name.lower()}_erased.shp"
        merged_gdf.to_file(shp_path)

        # After iterating, write a single table with all of the results to PostGIS
        print("Writing to postgis")
        db.import_gis(
            filepath=shp_path,
            sql_tablename=f"improvements.{county_name.lower()}_erased",
            explode=True,
            gpd_kwargs={"if_exists": "replace"},
        )


def split_features(db: Database, src_table: str = "improvements.cleaned_montgomery") -> None:
    """
    - In order to maintain network topology, we have to split every new line
    wherever it intersects another new line

    Arguments:
        src_table (str): name of the source geometry table

    Returns:
        None: but creates a new PostGIS table named 'improvements.montgomery_split'
    """

    all_gdfs = []

    query_template = f"""
        with source_line as (
            select uid, geom from {src_table}
            where uid = UID_PLACEHOLDER
        ),
        intersecting_lines as (
            select st_collect(c.geom) as geom
            from {src_table} c, source_line sl
            where st_intersects(
                c.geom, sl.geom
            )
            and c.uid != sl.uid
            and not c.geom = sl.geom
        )
        select 
            sl.uid as src_uid,
            (st_dump(
                st_split(
                    sl.geom,
                    il.geom
                )
            )).geom
        from source_line sl, intersecting_lines il
    """

    uids = db.query_as_list_of_singletons(f"select uid from {src_table}")

    for uid in tqdm(uids, total=len(uids)):

        query = query_template.replace("UID_PLACEHOLDER", str(uid))

        gdf = db.gdf(query)

        # If there's no result then this line didn't intersect anything
        # In this case we want to grab the original geometry
        if gdf.shape[0] == 0:
            new_query = f"""
                select uid, geom from {src_table}
                where uid = {uid}
            """
            gdf = db.gdf(new_query)

        all_gdfs.append(gdf)

    merged_gdf = pd.concat(all_gdfs)

    db.import_geodataframe(merged_gdf, "improvements.montgomery_split")


if __name__ == "__main__":
    db = pg_db_connection()
    erase_features(db)
    # split_features(db)

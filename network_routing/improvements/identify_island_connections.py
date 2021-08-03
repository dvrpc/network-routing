from tqdm import tqdm
import pg_data_etl as pg

from network_routing import pg_db_connection


def count_islands_connected_by_new_sidewalk(
    db: pg.Database,
    county_name: str = "Montgomery",
    segment_table: str = "improvements.montgomery_split",
    island_table: str = "data_viz.islands",
) -> None:
    """
    - Clip the regional island layer to the `county_name`
    - Evaluate each potential new sidewalk against the clipped islands
    - Save the number of distinct nearby islands as a column in the original table

    Arguments:
        db (pg.Database): analysis database
        county_name (str): name of the county to analyze, defaults to Montgomery
        segment_table (str): name of the table with new sidewalk geometries
        island_table (str): name of regional island analysis table

    Returns:
        None: but updates `segment_table` in-place with a `island_count` column
    """

    # Clip the regional island layer to a specific county,
    # ensuring that the resulting geometries have source ID intact
    # and have been exploded from multipart to singlepart features
    island_clip_query = f"""
        with county as (
            select geom 
            from regional_counties 
            where co_name = '{county_name}'
        )
        select
            i.uid as island_uid,
            i.size_miles,
            st_intersection(i.geom, c.geom) as geom
        from {island_table} i, county c
        where st_intersects(i.geom, c.geom)
    """

    clipped_island_tablename = f"improvements.islands_{county_name.lower()}"

    if clipped_island_tablename not in db.tables(spatial_only=True):
        gdf = db.gdf(island_clip_query)

        db.import_geodataframe(
            gdf,
            clipped_island_tablename,
            gpd_kwargs={"if_exists": "replace"},
            explode=True,
        )

    # Define a query template that will get used for every possible new sidewalk geometry
    # This query tells us how many distinct islands are within 15 meters of this feature
    query_template = f"""
        with main_geom as (
            select st_buffer(geom, 15) as geom
            from {segment_table}
            where uid = ID_PLACEHOLDER
        ),
        uid_list as (
            select distinct i.island_uid
            from
                {clipped_island_tablename} i,
                main_geom g
            where st_intersects(i.geom, g.geom)   
        )
        select count(island_uid)
        from uid_list
    """

    # Make sure the segment table has a column named 'island_count'
    db.execute(
        f"""
        ALTER TABLE {segment_table} ADD COLUMN IF NOT EXISTS island_count INT;
    """
    )

    # Get a list of all unique IDs for features without an island count yet
    uids = db.query_as_list_of_singletons(
        f"""
        SELECT uid
        FROM {segment_table}
        WHERE island_count IS NULL
    """
    )

    # Run the query template on each feature, saving result to DB before
    # moving on to the next iteration.
    for uid in tqdm(uids, total=len(uids)):
        query = query_template.replace("ID_PLACEHOLDER", str(uid))

        result = db.query_as_singleton(query)

        db.execute(
            f"""
            UPDATE {segment_table}
            SET island_count = {int(result)}
            WHERE uid = {uid}
        """
        )


if __name__ == "__main__":

    db = pg_db_connection()
    count_islands_connected_by_new_sidewalk(db)
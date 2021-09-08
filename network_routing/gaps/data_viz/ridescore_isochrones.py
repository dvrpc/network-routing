import pandas as pd
from tqdm import tqdm

from pg_data_etl import Database


def generate_isochrones(
    db: Database,
    sidewalk_result_table: str = "rs_sw.sw_results",
    osm_result_table: str = "rs_osm.osm_results",
    output_tablename: str = "data_viz.ridescore_results",
) -> None:
    """
    - Using the results of the OSM and Sidewalk ridescore analyses,
    generate two isochrones for each station (one OSM, one sidewalk).

    To use this process, you need to analyze the POIs by unique ID
    instead of by categories.

    Args:
        db (PostgreSQL): analysis database
        sidewalk_result_table (str): table with sidewalk network results
        osm_result_table (str): table with OpenStreetMap results
        output_tablename (str): name of the output table, with schema

    Returns:
        New SQL table is created named `output_tablename`
    """

    # output_schema, new_tablename = output_tablename.split(".")

    # Make sure that the output schema exists
    sql_query = f"CREATE SCHEMA IF NOT EXISTS {output_schema};"
    db.execute(sql_query)

    # Convert 1 mile to minutes
    miles = 1
    time_cutoff = miles * 60 / 2.5

    all_results = []

    ridescore_results = [
        sidewalk_result_table,
        osm_result_table,
    ]

    for result_table in ridescore_results:

        print(f"Generating isochrone for {result_table.upper()}")

        result_cols = db.columns(result_table)

        all_ids = [x[4:] for x in result_cols if "n_1_" in x]

        for poi_uid in tqdm(all_ids, total=len(all_ids)):
            # Figure out if there's results
            node_count_query = f"""
                SELECT COUNT(node_id)
                FROM {result_table}
                WHERE n_1_{poi_uid} <= {time_cutoff}
            """
            node_count = db.query_as_singleton(node_count_query)

            # Only make isochrones if there's nodes below the threshold
            if node_count > 0:

                # If there's only two points we want to extract
                # the linestring from the concavehull operation
                if node_count == 2:
                    geom_idx = 2
                # Otherwise, grab the polygon instead
                # See: https://postgis.net/docs/ST_CollectionExtract.html
                else:
                    geom_idx = 3

                query = f"""
                    select  st_buffer(
                                st_collectionextract(
                                    st_concavehull(st_collect(geom), 0.99),
                                    {geom_idx}),
                                45) as geom
                    from {result_table}
                    where n_1_{poi_uid} <= {time_cutoff}
                """
                gdf = db.query_as_geo_df(query)

                gdf["schema"] = result_table.split(".")[0]
                gdf["poi_uid"] = poi_uid

                gdf = gdf.rename(columns={"geom": "geometry"}).set_geometry("geometry")

                all_results.append(gdf)

    merged_gdf = pd.concat(all_results)

    db.import_geodataframe(merged_gdf, output_tablename)


def calculate_sidewalkscore(
    db: Database,
    poi_query: str,
    uid_col: str = "poi_uid",
    osm_schema: str = "rs_osm",
    sw_schema: str = "rs_sw",
    iso_table: str = "data_viz.ridescore_isos",
    output_tablename: str = "data_viz.ridescore",
) -> None:
    """
    - Using `data_viz.ridescore_pois`, generate a layer with a single point for each transit stop.

    - Update this layer with a columns `rs_sw` and `rs_osm` to hold attributes on how large
    the sidewalk and OSM isochrones are for the station.

    - Add another column, named `sidewalkscore`. This contains a ratio of the sidewalk walkshed
    size to the OSM walkshed size. This attribute is used for symbology on the webmap.

    Args:
        db (Database): analysis database
        poi_query (str): SQL query that provides the geom and uid of the source points
        uid_col (str): name of the ID column in the query, defaults to 'poi_uid'
        osm_schema (str): name of the OSM schema, defaults to 'rs_osm'
        sw_schema (str): name of the sidewalk schema, defaults to 'rs_sw'
        iso_table (str): name of the table with the isocrhone results, defaults to 'data_viz.ridescore_isos'
        output_tablename (str): name of the new point table that will be created, defaults to 'data_viz.ridescore'

    Returns:
        New SQL table is created named `output_tablename`

    """

    gdf = db.gdf(poi_query)

    gdf[osm_schema] = 0.0
    gdf[sw_schema] = 0.0

    for idx, row in tqdm(gdf.iterrows(), total=gdf.shape[0]):

        # Find all isochrones for this station
        query = f"""
            select schema, st_area(geom) as area
            from {iso_table}
            where {uid_col} = '{row.poi_uid}'
        """

        result = db.query_as_list_of_lists(query)

        # Drop each result into the appropriate column
        for colname, iso_area in result:
            gdf.at[idx, colname] = iso_area

    print(gdf)

    gdf["sidewalkscore"] = gdf[sw_schema] / gdf[osm_schema]

    db.import_geodataframe(gdf, output_tablename)

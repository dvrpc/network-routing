import pandas as pd
from tqdm import tqdm

from pg_data_etl import Database

from network_routing.gaps.data_viz.make_single_isochrone import generate_isochrones_for_single_table


def generate_isochrones(
    db: Database,
    sidewalk_result_table: str = "access_score_sw.sw_results",
    osm_result_table: str = "access_score_osm.osm_results",
    output_tablename: str = "data_viz.accessscore_results",
    sw_cutoff: float = 1.0,
    osm_cutoff: float = 1.0,
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
        sw_cutoff (float): the distance in miles to use for the sidewalk isochrones
        osm_cutoff (float): the distance in miles to use for the OSM isochrones

    Returns:
        New SQL table is created named `output_tablename`
    """

    output_schema, new_tablename = output_tablename.split(".")

    # Make sure that the output schema exists
    sql_query = f"CREATE SCHEMA IF NOT EXISTS {output_schema};"
    db.execute(sql_query)

    all_results = []

    ridescore_results = [
        {
            "tablename": sidewalk_result_table,
            "cutoff": sw_cutoff,
        },
        {
            "tablename": osm_result_table,
            "cutoff": osm_cutoff,
        },
    ]

    for result_config in ridescore_results:

        gdf = generate_isochrones_for_single_table(
            db,
            result_config["tablename"],
            mileage_cutoff=result_config["cutoff"],
        )

        all_results.append(gdf)

    merged_gdf = pd.concat(all_results)

    db.import_geodataframe(merged_gdf, output_tablename)


def calculate_sidewalkscore(
    db: Database,
    poi_query: str,
    uid_col: str = "poi_uid",
    osm_schema: str = "access_score_osm",
    sw_schema: str = "access_score_sw",
    iso_table: str = "data_viz.accessscore_results",
    output_tablename: str = "data_viz.accessscore_points",
) -> None:
    """
    - Generate a layer with a single point for each transit stop.

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

    gdf["sidewalkscore"] = gdf[sw_schema] / gdf[osm_schema]

    db.import_geodataframe(gdf, output_tablename)

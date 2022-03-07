import pandas as pd
import geopandas as gpd
from tqdm import tqdm

from pg_data_etl import Database


def generate_isochrones_for_single_table(
    db: Database,
    analysis_result_table: str,
    mileage_cutoff: float,
) -> gpd.GeoDataFrame:
    """
    - Generate a single isochrone for each analysis POI.

    To use this process, you need to analyze the POIs by unique ID
    instead of by categories.

    Args:
        db (PostgreSQL): analysis database
        analysis_result_table (str): table with network accessibility results
        mileage_cutoff (float): distance in miles to use as cutoff for isochrone shape

    Returns:
        gpd.GeoDataFrame
    """

    # Convert mileage cutoff to minutes
    time_cutoff = mileage_cutoff * 60 / 2.5

    all_results = []

    print(f"Generating isochrone for {analysis_result_table.upper()}")

    result_cols = db.columns(analysis_result_table)

    all_ids = [x[4:] for x in result_cols if "n_1_" in x]

    for poi_uid in tqdm(all_ids, total=len(all_ids)):
        # Figure out if there's results
        node_count_query = f"""
            SELECT COUNT(node_id)
            FROM {analysis_result_table}
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
                from {analysis_result_table}
                where n_1_{poi_uid} <= {time_cutoff}
            """
            gdf = db.gdf(query)

            gdf["schema"] = analysis_result_table.split(".")[0]
            gdf["poi_uid"] = poi_uid

            gdf = gdf.rename(columns={"geom": "geometry"}).set_geometry("geometry")

            all_results.append(gdf)

    merged_gdf = pd.concat(all_results)

    return merged_gdf


if __name__ == "__main__":
    from network_routing import pg_db_connection

    db = pg_db_connection()

    gdf = generate_isochrones_for_single_table(db, "delco.trailheads_results", 2)

    db.import_geodataframe(gdf, "data_viz.delco_isochrones_2miles")

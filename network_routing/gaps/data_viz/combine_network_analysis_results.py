import pandas as pd

from postgis_helpers import PostgreSQL


def combine_transit_results(db: PostgreSQL):

    # For each state, get the sidewalk nodes with the
    # walk time to the closest transit stop (of any kind)

    all_gdfs = []

    for schema in ["gaps_nj", "gaps_pa"]:

        # Get one row from the access results
        gdf_sample = db.query_as_geo_df(
            f"SELECT * FROM {schema}.all_transit_results LIMIT 1"
        )

        # Make a list of all columns that have 'n_1_' in their name
        cols_to_query = [col for col in gdf_sample.columns if "n_1_" in col]

        # Build a dynamic SQL query, getting the LEAST of the n_1_* columns
        query = "SELECT geom, LEAST(" + ", ".join(cols_to_query)
        query += f") as walk_time FROM {schema}.all_transit_results"

        gdf = db.query_as_geo_df(query)

        all_gdfs.append(gdf)

    combined_gdf = pd.concat(all_gdfs)

    db.import_geodataframe(combined_gdf, "results_transit_access", schema="data_viz")

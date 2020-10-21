import pandas as pd
from tqdm import tqdm

from transit_access import db

from sidewalk_gaps.accessibility.network_analysis import SidewalkNetwork


def calculate_sidewalk_walksheds():

    ridescore_arguments = {
        "poi_table_name": "ridescore_stations",
        "poi_id_column": "dvrpc_id",
        "output_table_name": "ridescore",
        "num_pois": 1,
        "poi_match_threshold": 152  # aka 500'
    }

    for schema in ["nj", "pa"]:
        print("Calculating sidewalk network distance for:", schema)
        network = SidewalkNetwork(db, schema, **ridescore_arguments)


def generate_isochrones():

    all_results = []

    # Convert 0.5 miles to minutes
    miles = 0.5
    time_cutoff = miles * 60 / 2.5

    for schema in ["nj", "pa"]:

        print(f"Generating isochrone for {schema.upper()}")

        result_cols = db.table_columns_as_list("ridescore_results", schema=schema)

        station_ids = [x[4:] for x in result_cols if "n_1_" in x]

        for dvrpc_id in tqdm(station_ids, total=len(station_ids)):
            # Figure out if there's results
            node_count_query = f"""
                SELECT COUNT(node_id)
                FROM {schema}.ridescore_results
                WHERE n_1_{dvrpc_id} <= {time_cutoff}
            """
            node_count = db.query_as_single_item(node_count_query)

            # Only make isochrones if there's nodes below the threshold
            if node_count > 0:

                query = f"""
                    select  st_buffer(
                                st_collectionextract(
                                    st_concavehull(st_collect(geom), 0.99),
                                    3),
                                45) as geom
                    from {schema}.ridescore_results
                    where n_1_{dvrpc_id} <= {time_cutoff}
                """
                gdf = db.query_as_geo_df(query)

                gdf["schema"] = schema
                gdf["dvrpc_id"] = dvrpc_id

                gdf = gdf.rename(columns={'geom': 'geometry'}).set_geometry('geometry')

                all_results.append(gdf)

    merged_gdf = pd.concat(all_results)

    db.import_geodataframe(merged_gdf, "ridescore_isos")

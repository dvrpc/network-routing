import pandas as pd
from tqdm import tqdm

from postgis_helpers import PostgreSQL


def generate_isochrones(db: PostgreSQL):

    # Make a schema for data viz products
    sql_query = "CREATE SCHEMA IF NOT EXISTS data_viz;"
    db.execute(sql_query)

    # Convert 1 mile to minutes
    miles = 1
    time_cutoff = miles * 60 / 2.5

    all_results = []

    ridescore_results = [
        ("rs_osm", "osm_results"),
        ("rs_sw", "sw_results")
    ]

    for schema, result_table in ridescore_results:

        print(f"Generating isochrone for {schema.upper()}")

        result_cols = db.table_columns_as_list(result_table, schema=schema)

        station_ids = [x[4:] for x in result_cols if "n_1_" in x]

        for dvrpc_id in tqdm(station_ids, total=len(station_ids)):
            # Figure out if there's results
            node_count_query = f"""
                SELECT COUNT(node_id)
                FROM {schema}.{result_table}
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
                    from {schema}.{result_table}
                    where n_1_{dvrpc_id} <= {time_cutoff}
                """
                gdf = db.query_as_geo_df(query)

                gdf["schema"] = schema
                gdf["dvrpc_id"] = dvrpc_id

                gdf = gdf.rename(columns={'geom': 'geometry'}).set_geometry('geometry')

                all_results.append(gdf)

    merged_gdf = pd.concat(all_results)

    db.import_geodataframe(merged_gdf, "ridescore_isos", schema="data_viz")

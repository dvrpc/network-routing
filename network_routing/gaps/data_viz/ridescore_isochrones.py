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

    ridescore_results = [("rs_osm", "osm_results"), ("rs_sw", "sw_results")]

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
                    from {schema}.{result_table}
                    where n_1_{dvrpc_id} <= {time_cutoff}
                """
                gdf = db.query_as_geo_df(query)

                gdf["schema"] = schema
                gdf["dvrpc_id"] = dvrpc_id

                gdf = gdf.rename(columns={"geom": "geometry"}).set_geometry("geometry")

                all_results.append(gdf)

    merged_gdf = pd.concat(all_results)

    db.import_geodataframe(merged_gdf, "ridescore_isos", schema="data_viz")


def calculate_sidewalkscore(db: PostgreSQL):
    gdf = db.query_as_geo_df("SELECT * FROM passengerrailstations")

    gdf["rs_osm"] = 0.0
    gdf["rs_sw"] = 0.0

    for idx, row in tqdm(gdf.iterrows(), total=gdf.shape[0]):

        # Find all isochrones for this station
        query = f"""
            select schema, st_area(geom) as area
            from data_viz.ridescore_isos
            where dvrpc_id = '{row.dvrpc_id}'
        """

        result = db.query_as_list(query)

        # Drop each result into the appropriate column
        for colname, iso_area in result:
            gdf.at[idx, colname] = iso_area

    print(gdf)

    gdf["sidewalkscore"] = gdf["rs_sw"] / gdf["rs_osm"]

    db.import_geodataframe(gdf, "sidewalkscore", schema="data_viz")

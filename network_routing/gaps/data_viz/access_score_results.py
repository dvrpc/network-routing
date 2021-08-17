import pandas as pd
import geopandas as gpd
from tqdm import tqdm

from pg_data_etl import Database

from network_routing import pg_db_connection, GDRIVE_DATA

# the RUNS dict contains the necessary tablenames/cutoff value
# for each of the three analysis runs
RUNS = {
    "osm": {
        "edge_table": "osm_edges_all",
        "result_table": "access_score_osm.osm_results",
        "cutoff_minutes": 48,
    },
    "bike": {
        "edge_table": "lowstress_islands",
        "result_table": "access_score_lts.lts_results",
        "cutoff_minutes": 48,
    },
    "ped": {
        "edge_table": "pedestriannetwork_lines",
        "result_table": "access_score_sw.sw_results",
        "cutoff_minutes": 24,
    },
}


def geodataframe_of_result_for_single_poi(
    db: Database,
    dvrpc_id: int,
    result_table: str,
    edge_table: str,
    id_column: str,
    cutoff_minutes: float,
) -> gpd.GeoDataFrame:
    """
    Get a multi-linestring output showing all edges that are within `cutoff_minutes`
    of a given Access Score POI, identified by its `dvrpc_id`.

    Arguments:
        db (Database): analysis database
        dvrpc_id (int): ID of the POI to analyze
        result_table (str): name of the table with the node-level access analysis results
        edge_table (str): name of the edge table that was used to generate the results
        id_column (str): name of the column in the node table with IDs
        cutoff_minutes (float): the number of minutes to use as threshold/cutoff

    Returns:
        gpd.GeoDataFrame: with the multipart geometry and the associated POI ID
    """

    matching_node_subquery = f"""
        select {id_column}::int
        from {result_table}
        where n_1_{dvrpc_id} <= {cutoff_minutes}
    """

    query = f"""
        select
            '{dvrpc_id}' as dvrpc_id,
            '{edge_table}' as src_network,
            st_collect(i.geom) as geom
        from
            {edge_table} i
        where 
            i.end_id in ({matching_node_subquery})
          and 
            i.start_id in ({matching_node_subquery})
    """

    return db.gdf(query)


def access_score_poi_ids(
    db: Database, poi_tablename: str = "access_score_final_poi_set", id_column: str = "dvrpc_id"
) -> list:
    """
    - Get a list of all unique IDs within the POI table
    """
    query = f"""
        select distinct {id_column}
        from {poi_tablename}
        order by {id_column}
    """
    return db.query_as_list_of_singletons(query)


def get_all_access_score_results_as_edges(
    db: Database,
    edge_table: str,
    result_table: str,
    cutoff_minutes: float,
    id_column: str = "node_id",
):
    """
    - Get results for all POIs for a given analysis network
    - Skip any IDs that didn't get a result on the network
    """

    all_ids = access_score_poi_ids(db)

    ids_in_table = [x.split("_")[-1] for x in db.columns(result_table) if "n_1_" in x]

    results = []
    no_results = []
    for poi_id in tqdm(all_ids, total=len(all_ids)):

        if str(poi_id) in ids_in_table:

            gdf = geodataframe_of_result_for_single_poi(
                db, poi_id, result_table, edge_table, id_column, cutoff_minutes
            )

            results.append(gdf)

        else:
            no_results.append(poi_id)

    if len(no_results) > 0:
        print(f"{edge_table} - no result for these POIs:")
        for uid in no_results:
            print(uid)

    return pd.concat(results)


def main():
    db = pg_db_connection()

    all_results = pd.concat(
        [
            get_all_access_score_results_as_edges(db, **RUNS["osm"]),
            get_all_access_score_results_as_edges(db, **RUNS["bike"]),
            get_all_access_score_results_as_edges(db, **RUNS["ped"]),
        ]
    )

    db.import_geodataframe(
        all_results, "data_viz.access_score_segments", gpd_kwargs={"if_exists": "replace"}
    )

    output_path = GDRIVE_DATA / "outputs/access_score_network_results.shp"
    db.export_gis(
        table_or_sql="data_viz.access_score_segments", filepath=output_path, filetype="shp"
    )


if __name__ == "__main__":
    main()

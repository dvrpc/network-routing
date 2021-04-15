from helpers import RoutableNetwork, db_connection

from postgis_helpers import PostgreSQL


def osm_analysis(db: PostgreSQL):

    arguments = {
        "poi_table_name": "ridescore_transit_poi_osm",
        "poi_id_column": "dvrpc_id",
        "output_table_name": "osm",
        "output_schema": "rs_osm",
        "num_pois": 1,
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "osm_edges_all",
        "node_table_name": "nodes_for_osm",
        "node_id_column": "node_id",
    }

    _ = RoutableNetwork(db, "public", **arguments)


def sidewalk_analysis(db: PostgreSQL):
    arguments = {
        "poi_table_name": "ridescore_transit_poi_sw",
        "poi_id_column": "dvrpc_id",
        "output_table_name": "sw",
        "output_schema": "rs_sw",
        "num_pois": 1,
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "pedestriannetwork_lines",
        "node_table_name": "nodes_for_sidewalks",
        "node_id_column": "sw_node_id",
    }

    _ = RoutableNetwork(db, "public", **arguments)


if __name__ == "__main__":
    db = db_connection()
    sidewalk_analysis(db)

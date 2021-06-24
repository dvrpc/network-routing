from __future__ import annotations

import pandas as pd

from pg_data_etl import Database

from .logic_prep import (
    assign_node_ids_to_network,
    add_travel_time_weights_to_network,
    construct_network,
)
from .logic_analyze import analyze_single_poi, get_unique_ids

from .logic_qaqc import clean_up_qaqc_tables, qaqc_poi_assignment


class RoutableNetwork:
    """
    - Build a routable network using `pandana` and analyze network-based
    distance to the N-nearest POI(s) by group.

    - This requires three input tables:

        1. Edges: linear features with valid topology
        2. Nodes: point features, one for each topological connection
        3. Points of Interest (POIs): point features showing locations to route people from. Must have an ID column to distinguish between the points.

    Attributes:
        db (PostgreSQL): database, the same thing returned from `network_routing.db_connection()`
        edge_table_name (str): name of the sidewalk, OSM, or other edge layer being analyzed
        node_table_name (str): name of nodes that correspond to the edge table
        node_id_column (str): name of unique ID column in the node table
        poi_table_name (str): name of POI table to analyze
        poi_id_column (str): name of ID column in the POI table, can be one or many features per ID. More than one feature for a given ID will get treated as a group.
        output_table_name (str): base tablename for results of analysis (network node geometry + accessibility attribute columns)
        output_schema (str): schema to store output analysis result + QAQC layers
        walking_mph (float): assumed pedestrian walking speed in miles-per-hour, defaults to `2.5`
        max_minutes (float): distance(/time) threshold to the analysis, defaults to `45`
        epsg (int): spatial data projection, defaults to `26918`
        num_pois (int): number of POIs to analyze when provided with groups (i.e. multiple features per ID), defaults to `3`
        poi_match_threshold (int): maximum allowable snapping distance between POI and node layers, defaults to `45`

    Returns:
        RoutableNetwork: network model
    """

    def __init__(
        self,
        db: Database,
        edge_table_name: str,
        node_table_name: str,
        node_id_column: str,
        poi_table_name: str,
        poi_id_column: str,
        output_table_name: str | None = None,
        output_schema: str | None = None,
        walking_mph: float = 2.5,
        max_minutes: float = 45,
        epsg: int = 26918,
        num_pois: int = 3,
        poi_match_threshold: int = 45,
    ):
        """
        Capture user input
        """

        # Database
        self.db = db

        # Edges
        self.edge_table_name = edge_table_name

        # Nodes
        self.node_table_name = node_table_name
        self.node_id_column = node_id_column

        # POIs
        self.poi_table_name = poi_table_name
        self.poi_id_column = poi_id_column

        # Output names
        self.output_table_name = output_table_name
        self.output_schema = output_schema

        # Analysis settings
        self.walking_mph = walking_mph
        self.max_minutes = max_minutes
        self.epsg = epsg
        self.num_pois = num_pois
        self.poi_match_threshold = poi_match_threshold

        # Get all unique POI ID values
        self.poi_ids = get_unique_ids(db, poi_table_name, poi_id_column)

        # Placeholders for network and geodataframes
        self.network = None
        self.edge_gdf = None
        self.node_gdf = None
        self.poi_gdf = None

    def build_network(self):
        """
        - Confirm that necessary columns exist in the edge table. Add them if they don't exist
        - Build network and save to memory
        """

        # Lint the edge table to confirm we have the columns we need
        # Run appropriate processes to create the columns if necessary

        edge_columns = self.db.columns(self.edge_table_name)

        if "start_id" not in edge_columns:
            assign_node_ids_to_network(
                self.db, self.edge_table_name, self.node_table_name, self.node_id_column
            )

        if "minutes" not in edge_columns:
            add_travel_time_weights_to_network(self.db, self.edge_table_name, self.walking_mph)

        # Build the network and save to memory

        self.network, self.edge_gdf, self.node_gdf = construct_network(
            self.db,
            self.edge_table_name,
            self.node_table_name,
            self.node_id_column,
            self.max_minutes,
        )

    def compute_single_poi(self, poi_uid: int | str, write_to_csv: bool = False):
        """
        - (build the network if it hasn't been built yet)
        - Calculate a single POI, identified by `poi_uid`
        - Write to CSV if `write_to_csv=True`
        """

        # Build the network if it doesn't yet exist
        if not self.network:
            self.build_network()

        return analyze_single_poi(
            self.db,
            self.network,
            poi_uid,
            self.poi_table_name,
            self.poi_id_column,
            self.edge_table_name,
            self.poi_match_threshold,
            self.max_minutes,
            self.num_pois,
            write_to_csv=write_to_csv,
        )

    def compute_every_poi_into_one_postgres_table(self):
        """
        - Calculate each unique ID in the POI table
        - Retain all results in-memory and write final result at end
        - This gives a nice tidy output, but will exceed RAM capacity with thousands of POIs
        - This is best used on 'smaller' POI inputs
        """

        # Build the network if it doesn't yet exist
        if not self.network:
            self.build_network()

        all_results = []

        poi_ids = get_unique_ids(self.db, self.poi_table_name, self.poi_id_column)

        total = len(poi_ids)
        counter = 0.0

        # Compute each individual POI
        for raw_id in poi_ids:

            counter += 1
            print("\t-> Working on", raw_id, "- pct complete:", round(counter / total * 100, 2))

            poi_gdf, result_df = self.compute_single_poi(raw_id)

            # If there are accessible nodes, make a QA table and add result data to running list
            if result_df is not None:
                clean_id = poi_ids[raw_id]
                qaqc_poi_assignment(
                    self.db, self.network, clean_id, poi_gdf, self.node_gdf, self.epsg
                )
                all_results.append(result_df)

        # Merge all results into a single dataframe
        df_all_access_results = pd.concat(all_results, axis=1, sort=False)

        # Write tabular result to postgres
        self.db.import_dataframe(
            df_all_access_results,
            f"{self.output_schema}.{self.output_table_name}_table",
            df_import_kwargs={"if_exists": "replace"},
        )

        # Generate geospatial version of results using node geometries
        final_result_query = f"""
            select r.*, n.geom
            from {self.node_table_name} n
            left join {self.output_schema}.{self.output_table_name}_table r
            on n.{self.node_id_column}::int = r.node_id::int
        """

        sql_tablename = f"{self.output_schema}.{self.output_table_name}_results"
        self.db.gis_make_geotable_from_query(final_result_query, sql_tablename, "Point", self.epsg)

        # Clean out QAQC tables by merging into one table in output schema, and delete temp tables
        clean_up_qaqc_tables(self.db, self.output_schema, self.poi_id_column)


class DoubleNetwork:
    """
    - `DoubleNetwork` allows you to test accessibility to a set of places against two networks
    - It uses two concurrent `RoutableNetwork` instances, writing results to CSV files on disk
    - `shared_args` must contain values for `poi_table_name` and `poi_id_column`

    Attributes:
        db (Database): analysis postgresql database
        shared_args (dict): any arguments that apply to both networks
        network_a_args (dict): arguments explicitly for the `A` network
        network_b_args (dict): arguments explicitly for the `B` network

    """

    def __init__(self, db: Database, shared_args: dict, network_a_args: dict, network_b_args: dict):
        """
        - Confirm that proper arguments have been provided and save them within the object
        """

        for colname in ["poi_table_name", "poi_id_column"]:
            if colname not in shared_args:
                print(f"You must specify a '{colname}' in the shared arguments")
                return None

        self.db = db
        self.shared_args = shared_args
        self.network_a_args = network_a_args
        self.network_b_args = network_b_args

        self.poi_table = shared_args["poi_table_name"]
        self.poi_id_column = shared_args["poi_id_column"]

        self.table_a_name = network_a_args["edge_table_name"]
        self.table_b_name = network_b_args["edge_table_name"]

    def compute(self):
        """
        - Build `A` and `B` networks from `RoutableNetworkLite`
        - Process every poi ID from the `poi_table`
        - Note: this can take a while depending on how many POIs you're processing
        - Keep an eye on your machine's resource usage, especially if you get cryptic error messages
        """
        print(f"Building {self.table_a_name.upper()} network")
        self.network_a = RoutableNetwork(self.db, **self.shared_args, **self.network_a_args)
        self.network_a.build_network()

        print(f"Building {self.table_b_name.upper()} network")
        self.network_b = RoutableNetwork(self.db, **self.shared_args, **self.network_b_args)
        self.network_b.build_network()

        # Get a list of all unique POI IDs in the table
        self.ids_to_process = self.db.query_as_list_of_singletons(
            f"""
            select distinct {self.poi_id_column}
            from {self.poi_table}
            order by  {self.poi_id_column};
        """
        )

        print("Analyzing each individual POI")
        counter = 0
        total = len(self.ids_to_process)

        for eta_uid in self.ids_to_process:

            counter += 1
            progress = round(counter / total * 100, 2)
            print(f" Working on #{eta_uid}\t {progress}% complete")

            self.network_a.compute_single_poi(eta_uid, write_to_csv=True)
            self.network_b.compute_single_poi(eta_uid, write_to_csv=True)

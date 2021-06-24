from pathlib import Path
from datetime import datetime
import pandas as pd
import pandana as pdna
import sqlalchemy

from pg_data_etl import Database

from network_routing import pg_db_connection


def construct_network(
    db: Database,
    node_table_name: str,
    edge_table_name: str,
    node_id_column: str,
    max_minutes: float,
):
    """
    - Turn PostGIS data into a pandana.network
    """

    # Get all edges
    query = f"""
        SELECT start_id, end_id, minutes, geom
        FROM {edge_table_name}
        WHERE start_id IN (
                select distinct {node_id_column}
                FROM {node_table_name}
            )
            AND
            end_id IN (
                select distinct {node_id_column}
                FROM {node_table_name}
            )
    """
    edge_gdf = db.gdf(query)

    # Get all nodes
    node_query = f"""
        SELECT {node_id_column} AS node_id,
            ST_X(st_transform(geom, 4326)) as x,
            ST_Y(st_transform(geom, 4326)) as y,
            geom
        FROM {node_table_name}
    """
    node_gdf = db.gdf(node_query)

    # Force the ID columns in the edge gdf to integer
    for col in ["start_id", "end_id"]:
        edge_gdf[col] = edge_gdf[col].astype(int)

    # Set the index of the NODE gdf to the uid column
    node_gdf.set_index("node_id", inplace=True)

    # Build the pandana network
    print("Making network")
    network = pdna.Network(
        node_gdf["x"],
        node_gdf["y"],
        edge_gdf["start_id"],
        edge_gdf["end_id"],
        edge_gdf[["minutes"]],
        twoway=True,
    )

    print("Precomputing the network")
    network.precompute(max_minutes)

    return network


class RoutableNetworkLite:
    """
    - `RoutableNetworkLite` is a lightweight implementation of `RoutableNetwork`
    - Instead of processing / storing everything in-memory and writing to Postgres upon completion,
    this version writes to CSV file every time a POI group is analyzed
    """

    def __init__(
        self,
        db: Database,
        schema: str,
        edge_table_name: str,
        node_table_name: str,
        node_id_column: str,
        poi_table_name: str,
        poi_id_column: str,
        walking_mph: float = 2.5,
        max_minutes: float = 45,
        epsg: int = 26918,
        num_pois: int = 1,
        poi_match_threshold: int = 45,
    ):

        # Capture user input
        self.db = db
        self.schema = schema
        self.walking_mph = walking_mph
        self.max_minutes = max_minutes
        self.epsg = epsg
        self.edge_table_name = edge_table_name
        self.node_table_name = node_table_name
        self.node_id_column = node_id_column
        self.poi_table_name = poi_table_name
        self.poi_id_column = poi_id_column
        self.num_pois = num_pois
        self.poi_match_threshold = poi_match_threshold

        # Confirm nodes & travel times exist on edge table
        self._setup()

        # Create network object from postgis data
        self.network = construct_network(
            self.db,
            self.node_table_name,
            self.edge_table_name,
            self.node_id_column,
            self.max_minutes,
        )

    def _setup(self):
        """
        Set up the analysis by:
            1) assigning node ids to the edge network
            2) adding travel time weights (walking)

        Only execute these functions if they haven't been run yet
        """

        edge_columns = self.db.columns(f"{self.schema}.{self.edge_table_name}")

        if "start_id" not in edge_columns:
            self._assign_node_ids_to_network()

        if "minutes" not in edge_columns:
            self._add_travel_time_weights()

    def _assign_node_ids_to_network(self):
        """
        Using the newly-created node table, we now
        need to assign two node_id values to each
        segment: one at the start, one at the end.
        """

        print("Assigning Node ID values to the edge table")

        # Add columns for the start and end node_id values
        for column_name in ["start_id", "end_id"]:
            self.db.execute(
                f"""
                ALTER TABLE {self.schema}.{self.edge_table_name}
                ADD COLUMN IF NOT EXISTS {column_name} INT;
            """
            )

        # Execute the query for the START of each segment
        start_id_query = f"""
            UPDATE {self.schema}.{self.edge_table_name} ln
            SET start_id = (SELECT pt.{self.node_id_column}
                            FROM {self.schema}.{self.node_table_name} pt
                            WHERE ST_DWITHIN(pt.geom, st_startpoint(ln.geom), 5)
                            ORDER BY ST_DISTANCE(pt.geom,
                                                st_startpoint(ln.geom))
                                    ASC LIMIT 1)
        """
        self.db.execute(start_id_query)

        # Execute the query for the END of each segment
        end_id_query = start_id_query.replace("start", "end")
        self.db.execute(end_id_query)

    def _add_travel_time_weights(self):
        """
        Add impedence columns to the edges.

            1) Calculate the legnth in meters (epsg:26918)
            2) Convert meters into minutes:
                - divide by 1609.34
                - divide by defined walking speed in MPH
                - multiply by 60 to get minutes
        """

        print("Adding travel time weights to the edge table")

        # Add a meter length and minutes column
        for column_name in ["len_meters", "minutes"]:
            self.db.execute(
                f"""
                ALTER TABLE {self.schema}.{self.edge_table_name}
                ADD COLUMN IF NOT EXISTS {column_name} FLOAT;
            """
            )

        # Capture length in meters into its own column
        update_meters = f"""
            UPDATE {self.schema}.{self.edge_table_name}
            SET len_meters = ST_LENGTH(geom);
        """
        self.db.execute(update_meters)

        # Calculate walking travel time in minutes
        update_minutes = f"""
            UPDATE {self.schema}.{self.edge_table_name}
            SET minutes = len_meters / 1609.34 / {self.walking_mph} * 60;
        """
        self.db.execute(update_minutes)

    def analyze_poi(self, poi_uid: int) -> None:

        # Get all POIs with this uid
        # that are within 'poi_match_threshold' meters of a sidewalk
        poi_query = f"""
            SELECT *,
                ST_X(st_transform(geom, 4326)) as x,
                ST_Y(st_transform(geom, 4326)) as y
            FROM {self.schema}.{self.poi_table_name}
            WHERE {self.poi_id_column} = '{poi_uid}'
            AND ST_DWITHIN(
                geom,
                (SELECT ST_COLLECT(geom) FROM {self.schema}.{self.edge_table_name}),
                {self.poi_match_threshold}
            )
        """
        poi_gdf = self.db.gdf(poi_query)

        # If there aren't any rows in the query result,
        # there are no POIs of this theme that are 'close enough'
        # to the sidewalk network.
        # Break out of function early if this happens.
        if poi_gdf.shape[0] == 0:
            return None

        # Assign the POIs to the network
        self.network.set_pois(
            category=str(poi_uid),
            x_col=poi_gdf["x"],
            y_col=poi_gdf["y"],
            maxdist=self.max_minutes,
            maxitems=self.num_pois,
        )

        # Calculate the distance across the network to this set of POIs
        df = self.network.nearest_pois(
            distance=self.max_minutes, category=str(poi_uid), num_pois=self.num_pois
        )

        # Clean up the column names into something distinct
        # i.e. '1' turns into 'n_1_ID' for a given ID, etc.
        new_colnames = {}
        for column in df.columns:
            new_name = f"n_{column}_{poi_uid}"
            new_colnames[column] = new_name

        df = df.rename(index=str, columns=new_colnames)

        # Filter results to values below max threshold
        # defaults to the closest (n = 1)
        df = df[df[f"n_1_{poi_uid}"] < self.max_minutes]

        # NOTE! Writing to CSV is 98% faster than writing to postgres (in this test)...
        # ... so we're writing CSVs as we go and saving to disk

        # Write result to CSV file on disk
        df.to_csv(f"./data/{self.edge_table_name}_{poi_uid}.csv")

        return None


class DoubleNetwork:
    """
    - `DoubleNetwork` allows you to test accessibility to a set of places against two networks
    - It uses two concurrent `RoutableNetworkLite` instances, writing results to CSV files on disk
    - `shared_args` must contain values for `poi_table_name` and `poi_id_column`

    Attributes:
        shared_args (dict): any arguments that apply to both networks
        network_a_args (dict): arguments explicitly for the `A` network
        network_b_args (dict): arguments explicitly for the `B` network

    """

    def __init__(self, shared_args: dict, network_a_args: dict, network_b_args: dict):
        """
        - Confirm that proper arguments have been provided and save them within the object
        """

        for colname in ["poi_table_name", "poi_id_column"]:
            if colname not in shared_args:
                print(f"You must specify a '{colname}' in the shared arguments")
                return None

        self.db = pg_db_connection()
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
        self.network_a = RoutableNetworkLite(self.db, **self.shared_args, **self.network_a_args)

        print(f"Building {self.table_b_name.upper()} network")
        self.network_b = RoutableNetworkLite(self.db, **self.shared_args, **self.network_b_args)

        self.ids_to_process = self.db.query_as_list_of_singletons(
            f"""
            select distinct {self.poi_id_column}
            from {self.poi_table}
            order by eta_uid;
        """
        )

        print("Analyzing each individual POI")
        counter = 0
        total = len(self.ids_to_process)

        for eta_uid in self.ids_to_process:

            counter += 1
            progress = round(counter / total * 100, 2)
            print(f" Working on #{eta_uid}\t {progress}% complete")

            self.network_a.analyze_poi(eta_uid)
            self.network_b.analyze_poi(eta_uid)


if __name__ == "__main__":

    dn = DoubleNetwork(
        shared_args={
            "schema": "public",
            "poi_table_name": "eta_montgomery",
            "poi_id_column": "eta_uid",
            "max_minutes": 45,
            "poi_match_threshold": 152,  # aka 500'
        },
        network_a_args={
            "edge_table_name": "osm_edges_all",
            "node_table_name": "nodes_for_osm_all",
            "node_id_column": "node_id",
        },
        network_b_args={
            "edge_table_name": "pedestriannetwork_lines",
            "node_table_name": "nodes_for_sidewalks",
            "node_id_column": "sw_node_id",
        },
    )

    dn.compute()

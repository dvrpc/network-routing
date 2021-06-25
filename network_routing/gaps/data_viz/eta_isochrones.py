from __future__ import annotations

import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm

import pg_data_etl as pg

from network_routing import pg_db_connection
from network_routing.accessibility.logic_analyze import get_unique_ids


class IsochroneGenerator:
    """
    - This class consumes the ouputs from `access eta-individual COUNTY`
    - It takes the node-level access analysis results and generates isochrones
    around each POI for both networks, sized to the specified distance threshold
    and walking speed

    Attributes:
        db (pg.Database): analysis database
        poi_table (str): name of the POI table
        poi_col (str): name of the unique ID column in the POI table
        network_a_edges (str): name of network 'A's edge table
        network_a_nodes (str): name of network 'A's node table
        network_a_node_id_col (str): name of ID column in network 'A's node table
        network_b_edges (str): name of network 'B's edge table
        network_b_nodes (str): name of network 'B's node table
        network_b_node_id_col (str): name of ID column in network 'B's node table
        distance_threshold_miles (float): distance to use for isochrones. Defaults to 1.0
        walking_speed_mph (float): Assumned walking speed of pedestrians, defaults to 2.5 mph
        data_dir (str): folder where outputs from earlier process were stored. Defaults to "./data"


    """

    def __init__(
        self,
        db: pg.Database,
        poi_table: str,
        poi_col: str,
        network_a_edges: str,
        network_a_nodes: str,
        network_a_node_id_col: str,
        network_b_edges: str,
        network_b_nodes: str,
        network_b_node_id_col: str,
        distance_threshold_miles: float = 1.0,
        walking_speed_mph: float = 2.5,
        data_dir: str = "./data",
    ):
        self.db = db
        self.data_dir = Path(data_dir)
        self.minutes_cutoff = distance_threshold_miles * 60 / walking_speed_mph
        self.data_names = {
            "a": {
                "edges": network_a_edges,
                "nodes": network_a_nodes,
                "node_id_col": network_a_node_id_col,
            },
            "b": {
                "edges": network_b_edges,
                "nodes": network_b_nodes,
                "node_id_col": network_b_node_id_col,
            },
            "poi": {"table": poi_table, "id_col": poi_col},
        }

        # Read all filenames for networks A and B
        tables = {
            "a": [x for x in self.data_dir.rglob(f"{network_a_edges}_*.csv")],
            "b": [x for x in self.data_dir.rglob(f"{network_b_edges}_*.csv")],
        }

        # For each POI ID, record A and B filepaths if they exist
        uids = get_unique_ids(db, poi_table, poi_col)

        self.uid_results = {
            raw_id: {"clean_id": clean_id, "a": None, "b": None}
            for raw_id, clean_id in uids.items()
        }

        for uid in self.uid_results:
            clean_id = uids[uid]
            a_path = self.data_dir / f"{network_a_edges}_{clean_id}.csv"
            b_path = self.data_dir / f"{network_b_edges}_{clean_id}.csv"

            if a_path in tables["a"]:
                self.uid_results[uid]["a"] = a_path

            if b_path in tables["b"]:
                self.uid_results[uid]["b"] = b_path

        # For each ID, gather node lists or None
        self.data = {
            k: {"a": self.load_data(v["a"]), "b": self.load_data(v["b"])}
            for k, v in self.uid_results.items()
        }

    def load_data(self, filepath: Path | None) -> tuple | None:
        """
        - Read CSV file from disk
        - Filter out rows beyond `self.minutes_cutoff`

        Arguments:
            filepath (Path | None): filepath to CSV file or None value

        Returns:
            tuple: if filepath is not None, read CSV with pandas and return a list of node IDs that meet the `minutes_cutoff`
        """
        if filepath:
            # Read CSV
            df = pd.read_csv(filepath)

            # Filter to only include rows that are at or below the
            # defined cutoff time in minutes
            df = df[df["n_1"] <= self.minutes_cutoff]

            # Get a list of the remaining node id values as a tuple
            nodes_as_tuple = tuple(df["node_id"].unique())

            return nodes_as_tuple

        else:
            return None

    def make_concave_hull(self, eta_uid: str) -> gpd.GeoDataFrame | None:
        """
        - Generate a set of concave hulls for a single UID, using networks A and B

        Arguments:
            eta_uid (str): ID of the POI

        Returns:
            gpd.GeoDataFrame: polygons for both networks, if there are results
        """

        # Only load node lists that exist. Skip 'None' values
        node_lists = {}
        for network_id in ["a", "b"]:
            data = self.data[eta_uid][network_id]
            if data:
                node_lists[network_id] = data

        gdfs = []

        for network_id, node_filter in node_lists.items():
            edge_table = self.data_names[network_id]["edges"]
            node_table = self.data_names[network_id]["nodes"]
            node_id_col = self.data_names[network_id]["node_id_col"]

            num_nodes = len(node_filter)

            if num_nodes > 0:

                # See: https://postgis.net/docs/ST_CollectionExtract.html
                if num_nodes == 1:
                    geom_idx = 1
                    node_filter = f"({node_filter[0]})"

                elif num_nodes == 2:
                    geom_idx = 2

                else:
                    geom_idx = 3

                query = f"""
                    select
                        '{eta_uid}' as eta_uid,
                        '{edge_table}' as src_network,
                        st_buffer(
                            st_collectionextract(
                                st_concavehull(
                                    st_collect(geom), 
                                    0.99
                                ),
                            {geom_idx}),
                        45) as geom
                    from {node_table}
                    where {node_id_col} in {node_filter}
                """

                gdfs.append(self.db.gdf(query))

        if len(gdfs) == 0:
            return None

        else:
            return pd.concat(gdfs)

    def isochrones(self) -> gpd.GeoDataFrame:
        """
        - Generate an isochrone set for every POI UID

        Returns:
            gpd.GeoDataFrame: a single gdf with all results merged together
        """

        print("Generating all isochrones")

        all_gdfs = []

        for eta_uid in tqdm(self.data.keys(), total=len(self.data)):
            iso = self.make_concave_hull(eta_uid)

            if iso is not None:
                all_gdfs.append(iso)

        gdf = pd.concat(all_gdfs)

        return gdf

    def save_isos_to_db(self) -> None:
        """
        - Save the full isochrone set to PostgreSQL

        Returns:
            None: but creates a new table named `f"data_viz.isochrones_{poi_tablename}"`
        """

        gdf = self.isochrones()

        print("Writing to PostgreSQL")

        poi_tablename = self.data_names["poi"]["table"]

        self.db.import_geodataframe(
            gdf, f"data_viz.isochrones_{poi_tablename}", gpd_kwargs={"if_exists": "replace"}
        )

    def save_pois_with_iso_stats_to_db(self) -> None:
        """
        - Value of -2 == no matches on either network
        - Value of -1 == A network matched but B did not
        - Value of 0 == B network matched but A did not
        - Value >0 == A and B matched, value is the actual ratio
        """
        poi_info = self.data_names["poi"]
        tablename = poi_info["table"]
        id_col = poi_info["id_col"]

        poi_gdf = self.db.gdf(f"select * from {tablename}")
        poi_gdf["ab_ratio"] = -2.0

        for idx, poi in poi_gdf.iterrows():
            this_id = poi[id_col]

            query = f"""
                select src_network, st_area(geom) as area
                from data_viz.isochrones_{tablename}
                where eta_uid = '{this_id}'
            """

            shape_info = self.db.query_as_list_of_lists(query)

            if len(shape_info) == 0:
                print("WARNING! No results for ID #", this_id)
            else:

                values = {
                    self.data_names["a"]["edges"]: 0,
                    self.data_names["b"]["edges"]: 0,
                }

                for result in shape_info:
                    edge_table, area = result
                    values[edge_table] = area

                a = values[self.data_names["a"]["edges"]]
                b = values[self.data_names["b"]["edges"]]

                if b == 0:
                    ratio = -1
                else:
                    ratio = a / b

                poi_gdf.at[idx, "ab_ratio"] = ratio

        self.db.import_geodataframe(
            poi_gdf, f"data_viz.ab_ratio_{tablename}", gpd_kwargs={"if_exists": "replace"}
        )


if __name__ == "__main__":
    db = pg_db_connection()

    args = {
        "db": db,
        "poi_table": "eta_montgomery",
        "poi_col": "eta_uid",
        "network_a_edges": "pedestriannetwork_lines",
        "network_a_nodes": "nodes_for_sidewalks",
        "network_a_node_id_col": "sw_node_id",
        "network_b_edges": "osm_edges_all",
        "network_b_nodes": "nodes_for_osm_all",
        "network_b_node_id_col": "node_id",
        "data_dir": "./data",
    }

    i = IsochroneGenerator(**args)

    # i.save_isos_to_db()
    i.save_pois_with_iso_stats_to_db()
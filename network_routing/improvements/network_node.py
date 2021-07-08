"""
"""
import pandas as pd
from tqdm import tqdm

from network_routing import pg_db_connection
from pg_data_etl import Database


class NetworkNodes:
    """
    This class exists to stitch a new set of edges into
    a pre-existing network of edges.

    Using the new edge's nodes, draw new connector lines to
    the old network's nodes.
    """

    def __init__(
        self,
        db: Database,
        new_nodes: str,
        new_node_uid_col: str,
        old_nodes: str,
        old_node_uid_col: str,
        new_edges: str,
        old_edges: str,
    ):
        self.db = db
        self.nodes = {
            "new": {"tbl": new_nodes, "col": new_node_uid_col},
            "old": {"tbl": old_nodes, "col": old_node_uid_col},
        }
        self.edges = {
            "new": new_edges,
            "old": old_edges,
        }

    def node_uids(self, table: str):

        values = self.nodes[table]

        tbl = values["tbl"]
        col = values["col"]

        return self.db.query_as_list_of_singletons(f"select {col} from {tbl};")

    def nearby_nodes(
        self, uid: int, n: int = 1, search_dist: float = 25.0, src: str = "new", dest: str = "old"
    ) -> list:
        """
        - Get the ID of the n-closest node within search_dist
        """
        query = f"""
            with src as (
                select geom from {self.nodes[src]['tbl']} where {self.nodes[src]['col']} = {uid}
            )
            select {self.nodes[dest]['col']}
            from {self.nodes[dest]['tbl']} dest, src
            where st_dwithin(
                dest.geom,
                src.geom,
                {search_dist}
            )
            order by st_distance(dest.geom, src.geom) asc
            limit {n}        
        """
        # print(query)
        result = self.db.query(query)
        if result:
            return result[n - 1][0]
        else:
            return None

    def uids_to_analyze(self, table: str = "new") -> list:
        """
        - Figure out which uids should be analyzed
        """
        query = f"""
            select
                nodes.{self.nodes[table]['col']}
            from
                {self.nodes[table]['tbl']} nodes
            left join
                {self.edges[table]} edges 
            on
                st_intersects(nodes.geom, edges.geom) 
            group by
                nodes.{self.nodes[table]['col']}
            having
                count(edges.*) = 1
        """
        return self.db.query_as_list_of_singletons(query)

    def draw_lines(self, from_table: str = "new", to_table: str = "old"):
        print(f"Handling {from_table.upper()} nodes to {to_table.upper()} nodes")

        from_tablename = self.nodes[from_table]["tbl"]
        from_uid_col = self.nodes[from_table]["col"]

        to_tablename = self.nodes[to_table]["tbl"]
        to_uid_col = self.nodes[to_table]["col"]

        print("Screening nodes to analyze")
        uids_to_analyze = self.uids_to_analyze(from_table)

        flows = {}
        print("Finding src nodes with dest nodes nearby")
        for src_uid in tqdm(uids_to_analyze, total=len(uids_to_analyze)):

            dest_uid = self.nearby_nodes(src_uid, src=from_table, dest=to_table)

            if dest_uid:
                flows[src_uid] = dest_uid

        all_results = []
        print("Generating flow lines from each src -> dest")
        for src_uid, dest_uid in tqdm(flows.items(), total=len(flows)):
            query = f"""
                    with src as (
                        select {from_uid_col}, geom
                        from {from_tablename}
                        where {from_uid_col} = {src_uid}
                    ),
                    dest as (
                        select {to_uid_col}, geom
                        from {to_tablename}
                        where {to_uid_col} = {dest_uid}
                    )
                    select
                        src.{from_uid_col} as src_id,
                        dest.{to_uid_col} as dest_id,
                        '{from_table} to {to_table}' as tables,
                        st_makeline(src.geom, dest.geom) as geom
                    from
                        src, dest
                """
            gdf = self.db.gdf(query)
            all_results.append(gdf)

        print("Merging results")
        merged_gdf = pd.concat(all_results)
        self.db.import_geodataframe(merged_gdf, "improvements.montgomery_connectors")


if __name__ == "__main__":
    db = pg_db_connection()

    nn = NetworkNodes(
        db,
        "improvements.montco_new_nodes",
        "node_id",
        "nodes_for_sidewalks",
        "sw_node_id",
        "improvements.montgomery_split",
        "pedestriannetwork_lines",
    )

    nn.draw_lines()
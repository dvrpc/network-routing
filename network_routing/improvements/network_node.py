"""
"""
from __future__ import annotations

import click
import pandas as pd
from tqdm import tqdm

from pg_data_etl import Database

from network_routing import pg_db_connection


@click.command()
@click.argument("connect_to")
def reconnect_nodes(connect_to: str):
    """
    Draw connection lines between the new nodes and the existing nodes
    """
    if connect_to.upper() not in ["NEW", "OLD"]:
        print("The argument you provided is not configured. Choose from 'NEW' or 'OLD'")
        print(f"You chose: {connect_to}")
        return None

    db = pg_db_connection()

    kwargs = {
        "new_nodes": "improvements.montco_new_nodes",
        "new_node_uid_col": "node_id",
        "old_nodes": "nodes_for_sidewalks",
        "old_node_uid_col": "sw_node_id",
        "new_edges": "improvements.montgomery_split",
        "old_edges": "pedestriannetwork_lines",
    }

    nn = NetworkNodes(db, **kwargs)
    nn.draw_lines(to_table=connect_to.lower())


class NetworkNodes:
    """
    This class exists to stitch a new set of edges into
    a pre-existing network of edges.

    Using the new edge's nodes, draw new connector lines to
    the old network's nodes.

    This process can also be used to draw connector lines within a single table

    Parameters:
        db (Database): analysis database
        new_nodes (str): name of the table with the 'new' nodes
        new_node_uid_col  (str): name of the column in the new table that has unique IDs
        old_nodes (str): name of the table with the 'old' nodes
        old_node_uid_col  (str): name of the column in the old table that has unique IDs
        new_edges (str): name of the 'new' edge table
        old_edges (str): name of the 'old' edge table
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

    def node_uids(self, table: str) -> list:
        """
        - Get a list of every unique ID within the 'new' or 'old' node table

        Arguments:
            table (str): key for the table to use. Options include 'new' and 'old'

        Returns:
            list: with each item in the list being a unique ID for the table
        """

        values = self.nodes[table]

        tbl = values["tbl"]
        col = values["col"]

        return self.db.query_as_list_of_singletons(f"select {col} from {tbl};")

    def nearby_nodes(
        self,
        uid: int,
        src: str = "new",
        dest: str = "old",
        n: int = 1,
        search_dist: float = 25.0,
    ) -> list | None:
        """
        - Get the ID of the n-closest node within search_dist
        - If src and dest are the same table, choose the closest node that does not share the unique ID

        Arguments:
            uid (int): the unique ID of the node to analyze
            src (str): key for the table to use. Options include 'new' and 'old'
            dest (str): key for the table to use. Options include 'new' and 'old'
            n (int): number of results to return. Defaults to 1
            search_dist (float): map units for search tolerance. Defaults to 25 (meters)

        Returns:
            list | None: list with N-nearest node IDs, or None if there aren't any
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
            )"""

        # If source and destination are the same, make
        # sure that we don't select the same node
        if src == dest:
            query += f"""
            and {self.nodes[src]['col']} != {uid}
        """

        # All queries are ordered by distance and limited to N results
        query += f"""
            order by st_distance(dest.geom, src.geom) asc
            limit {n}        
        """

        result = self.db.query_as_list_of_singletons(query)

        if result:
            return result
        else:
            return None

    def uids_to_analyze(self, table: str = "new") -> list:
        """
        - Figure out which uids should be analyzed
        - Find all nodes that intersect only one edge line, and return unique ID value for each

        Arguments:
            table (str): key for the table to use. Options include 'new' and 'old'

        Returns:
            list: that includes unique ID values of each node on a dangling network edge
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

    def draw_lines(self, from_table: str = "new", to_table: str = "old", n: int = 1) -> None:
        """
        - Draw straight line from the 'from_table' nodes to the 'new_table' nodes
        - Steps:
            1) find dangling nodes
            2) identify N-nearest node ids for each result of #1
            3) draw lines between all results from #2
            4) save result of #3 to database

        Arguments:
            from_table (str): key for the table to use. Options include 'new' and 'old'
            to_table (str): key for the table to use. Options include 'new' and 'old'
            n (int): number of nearest nodes to find/draw lines for. Defaults to 1

        Returns:
            None: but writes result to new spatial table in database
        """
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

            dest_uid_list = self.nearby_nodes(src_uid, src=from_table, dest=to_table, n=n)

            for dest_uid in dest_uid_list:
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
        output_tablename = "improvements.montgomery_connectors_to_" + to_tablename.replace(".", "_")
        self.db.import_geodataframe(
            merged_gdf, output_tablename, gpd_kwargs={"if_exists": "replace"}
        )

"""
"""
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
    ):
        self.db = db
        self.new_nodes = new_nodes
        self.old_nodes = old_nodes
        self.new_node_uid_col = new_node_uid_col
        self.old_node_uid_col = old_node_uid_col

    def new_node_uids(self, table: str):
        if table == "new":
            col = self.new_node_uid_col
            tbl = self.new_nodes

        elif table == "old":
            col = self.new_node_uid_col
            tbl = self.new_nodes

        else:
            return None

        return db.query_as_list_of_singletons(f"select {col} from {tbl};")

    def nearby_nodes(self, uid: int, search_dist: float) -> list:
        """Get list of all nodes within search_dist"""
        query = f"""
        
        """
        pass

    def nearest_node(self):
        """Get the single closest node"""
        pass

    def connected_segments(self) -> list:
        """Get a list of all segments that intersect this node"""
        pass


if __name__ == "__main__":
    db = pg_db_connection()

    nn = NetworkNodes(
        db, "improvements.montco_new_nodes", "node_id", "nodes_for_sidewalks", "sw_node_id"
    )

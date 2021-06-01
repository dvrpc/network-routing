"""
"""
from postgis_helpers.PgSQL import PostgreSQL

from network_routing import db_connection

_db = db_connection()


class NetworkNode:
    def __init__(self, uid: int, db: PostgreSQL = _db):
        self.uid = uid
        self.db = db

    def nearby_nodes(self, search_dist: float) -> list:
        """Get list of all nodes within search_dist"""
        query = f""" """
        pass

    def nearest_node(self):
        """Get the single closest node"""
        pass

    def connected_segments(self) -> list:
        """Get a list of all segments that intersect this node"""
        pass

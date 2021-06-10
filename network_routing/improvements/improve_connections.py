"""
1) Combine the existing SW network with the improvement_concept table
2) Generate a new table where the overlapping geometries have been split @ intersections
3) Generate nodes to match the newly split line table
4) Turn these edges & nodes into a network
5) Find nodes in the network that have nearby disconnected nodes
"""

from network_routing import db_connection
from .network_node import NetworkNode


if __name__ == "__main__":

    db = db_connection()

    node = NetworkNode(123456)
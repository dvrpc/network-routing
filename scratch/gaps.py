from tqdm import tqdm

from postgis_helpers import PostgreSQL
from sidewalk_gaps.network_analysis import SidewalkNetwork
from datetime import datetime

from sidewalk_gaps import CREDENTIALS

themes_of_interest = [
    "artsentertainment",
    "business",
    "fooddrink",
    "school",
    "recreation",
]


if __name__ == "__main__":
    schema = "nj"
    state = "New Jersey"

    db = PostgreSQL(
        "sidewalk_gaps",
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )

    network = SidewalkNetwork(db, schema, run_on_create=False)

    big = 60
    medium = 15
    small = 1

    # # Add a hexagon layer covering the nodes
    # for size in [big, medium, small]:
    #     network.db.make_hexagon_overlay(f"hex_{size}", f"{schema}.nodes", 26918, size)

    # Find untouchable node ids
    query_parts = []
    for theme in themes_of_interest:
        query = f"""
            SELECT node_id::int FROM {schema}.poi_{theme} WHERE n_1 >= 180
        """
        query_parts.append(query)

    query = " UNION ".join(query_parts)

    query += """
        GROUP BY node_id
    """

    outer_query = f"""
        SELECT * FROM {schema}.nodes
        WHERE node_id IN ({query})
    """

    network.db.make_geotable_from_query(outer_query, "untouchable_nodes", "Point", 26918)

    print(query)
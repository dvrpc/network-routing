from postgis_helpers import PostgreSQL
from sidewalk_gaps.network_analysis import SidewalkNetwork

if __name__ == "__main__":
    from sidewalk_gaps import CREDENTIALS

    schema = "nj"

    db = PostgreSQL(
        "sidewalk_gaps",
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )

    network = SidewalkNetwork(db, schema)

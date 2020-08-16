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

    # Add a hexagon layer covering the nodes
    for size in [big, medium, small]:
        network.db.make_hexagon_overlay(f"hex_{size}", f"{schema}.nodes", 26918, size)

    # For the BIG hexagons, analyze anything in the state
    gdf = network.db.query_as_geo_df(f"""
        SELECT * FROM {schema}.hex_{big}
        WHERE ST_INTERSECTS(geom, (select st_convexhull(st_collect(geom)) from {schema}.centerlines))
    """)

    for theme in themes_of_interest:
        gdf[theme] = 0.0

    for idx, row in tqdm(gdf.iterrows(), total=gdf.shape[0]):
        inner_query = f"""
            SELECT geom FROM {schema}.hex_{big}
            WHERE gid = {row.gid}
        """
        
        for theme in themes_of_interest:

            query = f"""
                SELECT count(n_1) FROM {schema}.poi_{theme}
                WHERE st_within(geom, ({inner_query}))
                AND n_1 = 180
            """

            result = network.db.query_as_single_item(query)

            gdf.at[idx, theme] = result

    network.db.import_geodataframe(gdf, f"hex_{big}_result")

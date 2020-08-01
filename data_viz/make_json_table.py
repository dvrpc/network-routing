from postgis_helpers import PostgreSQL
from sidewalk_gaps import CREDENTIALS

database_name = "sidewalk_gaps"


if __name__ == "__main__":
    db = PostgreSQL(
        database_name,
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )

    tbl = "nj_centerline"

    query = """
        SELECT 
            seg_guid,
            sidewalk_3 * 3.28084 AS sw_feet,
            st_length(geom) * 3.28084 AS cl_feet,
            sidewalk_3 / st_length(geom) / 2 AS sw_coverage
        FROM nj_centerline
        WHERE sidewalk_3 IS NOT NULL
            AND seg_guid != '{131D6750-1708-11E3-B5F2-0062151309FF}'
    """

    df = db.query_as_df(query)

    df.to_json("centerline_classification.js",  orient="records")

    # df.to_file("data_viz/data/sidewalk_classification.json", driver="GeoJSON")
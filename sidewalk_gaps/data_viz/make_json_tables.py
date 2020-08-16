from postgis_helpers import PostgreSQL
from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME


def make_segment_table(db: PostgreSQL):
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


def make_network_table(db: PostgreSQL):
    query = """
        SELECT
            node_id,
            n_1_school AS school
        FROM nj.access_results
    """

    df = db.query_as_df(query)

    df.to_json("network_school_dist.js",  orient="records")


if __name__ == "__main__":
    db = PostgreSQL(
        PROJECT_DB_NAME,
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )
    # make_segment_table(db)
    make_network_table(db)

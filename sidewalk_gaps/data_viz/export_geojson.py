from postgis_helpers import PostgreSQL
from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME


def export_segments(db: PostgreSQL):
    query = """
        select
            sidewalk / st_length(geom) / 2 as sw,
            st_transform(geom, 4326) as geom
        from nj.centerlines
        union
        select
            sidewalk / st_length(geom) / 2 as sw,
            st_transform(geom, 4326) as geom
        from pa.centerlines
    """

    df = db.query_as_geo_df(query)

    df.to_file("/Users/aaron/centerline_classification.geojson",  driver="GeoJSON")


if __name__ == "__main__":
    db = PostgreSQL(
        PROJECT_DB_NAME,
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )
    export_segments(db)

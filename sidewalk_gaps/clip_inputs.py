"""
Summary of ``clip_inputs.py``
-----------------------------

Use the table ``municipalboundaries`` to clip
out the sidewalk network within a buffer distance.
"""
from postgis_helpers import PostgreSQL


def clip_inputs(db: PostgreSQL,
                state: str,
                municipality: str = None,
                buffer_meters: float = None):

    # Build up a SQL query that might buffer and/or include
    # a single municipality name
    if buffer_meters:
        place_query = f"SELECT st_union(st_buffer(geom, {buffer_meters})) "
    else:
        place_query = "SELECT st_union(geom) "

    place_query += f"""
        FROM municipalboundaries
        WHERE state = '{state.upper()}'
    """

    if municipality:
        place_query += f" AND UPPER(mun_label) = '{municipality.upper()}' "

    # Make a database schema for this clip
    if municipality:
        schema = municipality.lower().replace(" ", "_")
    else:
        schema = state.lower()

    db.execute(f"""
        DROP SCHEMA IF EXISTS {schema} CASCADE;
        CREATE SCHEMA {schema};
    """)

    data_to_clip = [
        ("pedestriannetwork_lines", "LineString"),
        ("points_of_interest", "Point"),
    ]

    for tbl_name, geom_type in data_to_clip:

        print(f"Clipping {tbl_name}")

        clip_query = f"""
            CREATE TABLE {schema}.{tbl_name} AS
            SELECT * FROM {tbl_name} t
            WHERE ST_INTERSECTS(t.geom, ({place_query}))
        """
        db.execute(clip_query)

        index_query = f"""
            CREATE INDEX ON {schema}.{tbl_name}
            USING GIST (geom);
        """
        db.execute(index_query)

        update_geom_table = f"""
            ALTER TABLE {schema}.{tbl_name}
            ALTER COLUMN geom TYPE geometry({geom_type}, 26918)
            USING ST_Transform(ST_SetSRID( geom, 26918), 26918);
        """
        db.execute(update_geom_table)


if __name__ == "__main__":
    import postgis_helpers as pGIS
    from sidewalk_gaps import CREDENTIALS

    db = pGIS.PostgreSQL("sidewalk_gaps", verbosity="minimal", **CREDENTIALS["localhost"])

    clip_inputs(db, "nj", "camden")

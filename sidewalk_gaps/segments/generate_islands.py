from random import randint

from postgis_helpers import PostgreSQL


def _random_rgb(a: float = 1.0) -> str:
    """Generate a random RGB value, with an option for transparency

    Output is something like: 'rgba(5, 167, 230, 1.0)'
    """
    r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
    return f"rgba({r}, {g}, {b}, {a})"


def generate_islands(db: PostgreSQL, schema: str = None):
    """Use the sidewalk layer to merge intersecting geometries.
    The output is a layer with one feature per 'island'
    It also has a column for size of island and a randomly-generated RGB value.
    """

    full_table_name = "pedestriannetwork_lines" if not schema else f"{schema}.sidewalks"
    output_schema = "data_viz" if not schema else schema

    query = f"""
        SELECT
            ST_COLLECTIONEXTRACT(
                UNNEST(ST_CLUSTERINTERSECTING(geom)),
                2
            ) AS geom
        FROM {full_table_name}
    """
    db.make_geotable_from_query(
        query, "islands", "MULTILINESTRING", 26918, schema=output_schema
    )

    # Add a column for size
    db.table_add_or_nullify_column(
        "islands", "size_miles", "FLOAT", schema=output_schema
    )

    query = f"UPDATE {output_schema}.islands SET size_miles = ST_LENGTH(geom) * 0.000621371;"
    db.execute(query)

    # For each island, make a rgba() string with random values

    # Add a column for rgba
    db.table_add_or_nullify_column("islands", "rgba", "TEXT", schema=output_schema)

    # Iterate over each feature. Make a random rgb code for each one
    query = f"SELECT uid FROM {output_schema}.islands"
    uids = db.query_as_df(query)
    for idx, row in uids.iterrows():

        rgba = _random_rgb()

        query = f"""
            UPDATE {output_schema}.islands
            SET rgba = '{rgba}'
            WHERE uid = {row.uid}
        """
        db.execute(query)

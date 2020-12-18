from postgis_helpers import PostgreSQL


def generate_islands(db: PostgreSQL, schema: str):
    """Use the sidewalk layer to merge intersecting geometries.
    The output is a layer with one feature per 'island'"""

    query = f"""
        SELECT
            ST_COLLECTIONEXTRACT(
                UNNEST(ST_CLUSTERINTERSECTING(geom)),
                2
            ) AS geom
        FROM {schema}.sidewalks
    """
    db.make_geotable_from_query(
        query, "islands", "MULTILINESTRING", 26918, schema=schema
    )

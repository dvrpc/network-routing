from postgis_helpers import PostgreSQL


def generate_nodes(db: PostgreSQL, edge_tbl: str, schema: str, geotable_kwargs: dict):
    """
    Query out all unique nodes within an edge table
    Save the result to database
    """

    node_query = f"""
        SELECT st_startpoint(geom) AS geom
        FROM {schema}.{edge_tbl} 
        UNION
        SELECT st_endpoint(geom) AS geom
        FROM {schema}.{edge_tbl}
        GROUP BY geom
    """

    db.make_geotable_from_query(node_query, schema=schema, **geotable_kwargs)

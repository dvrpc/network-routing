from pg_data_etl import Database


def generate_nodes(db: Database, edge_tbl: str, geotable_kwargs: dict):
    """
    Query out all unique nodes within an edge table
    Save the result to database
    """

    node_query = f"""
        SELECT st_startpoint(geom) AS geom
        FROM {edge_tbl} 
        UNION
        SELECT st_endpoint(geom) AS geom
        FROM {edge_tbl}
        GROUP BY geom
    """

    db.gis_make_geotable_from_query(node_query, **geotable_kwargs)

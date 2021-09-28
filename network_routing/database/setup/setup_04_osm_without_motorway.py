from network_routing import pg_db_connection


def setup_04_remove_motorways_from_osm():
    """
    Generate OSM layers that omit any features tagged 'motorway'
    """
    db = pg_db_connection()

    for src_table in ["osm_edges_all", "osm_edges_drive"]:
        if src_table in db.tables():
            query = f"""
                select * from {src_table}
                where highway not like '%%motorway%%'
            """

            db.gis_make_geotable_from_query(
                query, f"{src_table}_no_motorway", geom_type="LineString", epsg=26918
            )


if __name__ == "__main__":
    setup_04_remove_motorways_from_osm()

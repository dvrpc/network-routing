from network_routing import pg_db_connection
from .get_osm import import_osm_for_dvrpc_region


def setup_02_import_osm_drive_network():
    """
    Import the OpenStreetMap 'drive' network
    """

    db = pg_db_connection()

    import_osm_for_dvrpc_region(db, "drive")


if __name__ == "__main__":
    setup_02_import_osm_drive_network()

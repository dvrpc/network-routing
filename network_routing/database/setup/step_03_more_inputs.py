from network_routing import db_connection, GDRIVE_SW_GAPS_PROJECT_ROOT


def setup_03_import_mode_data():
    """
    Import DVRPC's 'Equity Through Access' point dataset
    """
    shp_path = GDRIVE_SW_GAPS_PROJECT_ROOT / "data-to-import" / "eta_essential_services.shp"

    db = db_connection()

    db.import_geodata("eta_points", shp_path)


if __name__ == "__main__":
    setup_03_import_mode_data()

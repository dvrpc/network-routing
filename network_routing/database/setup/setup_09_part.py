from network_routing import pg_db_connection, GDRIVE_DATA


def setup_09_import_part_data():
    """
    Import PART stop (poi) data
    """

    db = pg_db_connection()

    shapefile_folder = GDRIVE_DATA / "inputs/PART"
    for shp in shapefile_folder.rglob("*.shp"):
        db.import_gis(filepath=shp, sql_tablename=shp.stem.lower())


if __name__ == "__main__":
    setup_09_import_part_data()

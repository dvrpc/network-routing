from network_routing import pg_db_connection, GDRIVE_DATA


def setup_09_import_part_data():
    """
    Import PART stop (poi) data
    """

    db = pg_db_connection()

    shapefile_folder = GDRIVE_DATA / "inputs/PART"
    for shp in shapefile_folder.rglob("*.shp"):
        db.import_gis(
            filepath=shp, sql_tablename=shp.stem.lower(), gpd_kwargs={"if_exists": "replace"}
        )

    # Clean up the point layer:
    # remove the 'level_0' column from the raw data
    query = """
        ALTER TABLE part
        DROP COLUMN IF EXISTS level_0;
    """
    db.execute(query)


if __name__ == "__main__":
    setup_09_import_part_data()

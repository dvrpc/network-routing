from network_routing import pg_db_connection, GDRIVE_DATA


def setup_11_import_docks_data():
    """
    Import dock data
    """

    db = pg_db_connection()

    shapefile_folder = GDRIVE_DATA / "inputs/Docks"
    for shp in shapefile_folder.rglob("*.shp"):
        db.import_gis(
            filepath=shp, sql_tablename=shp.stem.lower(), gpd_kwargs={"if_exists": "replace"}
        )

    # Clean up the point layer:
    # remove the 'level_0' column from the raw data
    query = """
        ALTER TABLE docks
        DROP COLUMN IF EXISTS level_0;
    """
    db.execute(query)

    query2 = """  
        ALTER TABLE docks 
        ALTER COLUMN geom 
        TYPE Geometry(Point, 26918) 
        USING ST_Transform(geom, 26918);
    """
    db.execute(query2)

if __name__ == "__main__":
    setup_11_import_docks_data()

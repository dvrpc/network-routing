from network_routing import pg_db_connection, GDRIVE_DATA


def setup_07_import_srts_projects():
    """
    Import MCPC Safe Routes to School shapefile from GoogleDrive
    """
    db = pg_db_connection()

    shp_path = GDRIVE_DATA / "inputs/MCPC SRTS lines/MCPC_SRTS_Recs_Post_manual_edits.shp"

    db.import_gis(
        filepath=shp_path, sql_tablename="mcpc_srts_projects", gpd_kwargs={"if_exists": "replace"}
    )


if __name__ == "__main__":
    setup_07_import_srts_projects()

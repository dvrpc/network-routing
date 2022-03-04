from network_routing import pg_db_connection, GDRIVE_DATA


def setup_12_import_delco_trailheads():
    """
    Import Delaware County trailhead data
    """

    db = pg_db_connection()

    shapefile_folder = GDRIVE_DATA / "inputs/Delco Trail Project"
    for shp in shapefile_folder.rglob("*.geojson"):
        print(shp)
        db.import_gis(
            filepath=shp, sql_tablename=shp.stem.lower(), gpd_kwargs={"if_exists": "replace"}
        )

        db.gis_table_update_spatial_data_projection(
            "delco_trailheads", old_epsg=4326, new_epsg=26918, geom_type="Point"
        )

        db.execute(
            """
            alter table delco_trailheads
            drop column level_0;
        """
        )


if __name__ == "__main__":
    setup_12_import_delco_trailheads()

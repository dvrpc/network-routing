from network_routing import pg_db_connection, GDRIVE_DATA


def setup_08_import_septa_data():
    """
    Import SEPTA's regional rail, 15-minute bus network, and heavy/light rail stations
    and merge them all into one layer named 'pois_for_septa_tod_analysis'
    """
    db = pg_db_connection()

    data_folder = GDRIVE_DATA / "inputs/SEPTA request"

    # Import shapefiles from GDrive folder
    for shp_filepath in data_folder.rglob("*.shp"):
        print(shp_filepath.stem)

        db.import_gis(filepath=shp_filepath, sql_tablename=shp_filepath.stem.lower())

    # Run a query that combines all three tables into one singular table
    # the 'stop_id' column across all three tables should be unique
    query = """
        select
            '15minnetwork' as src_table,
            stop_id::text,
            st_transform(geom, 26918) as geom
        from septa_15minnetwork_proj

        union

        select
            'heavynlight' as src_table,
            stop_id::text,
            st_transform(geom, 26918) as geom
        from septa_heavynlightrail_proh

        union

        select
            'regional' as src_table,
            stop_id::text,
            st_transform(geom, 26918) as geom
        from septa_regional_proj srp 
    """

    db.gis_make_geotable_from_query(query, "pois_for_septa_tod_analysis", "POINT", 26918)


if __name__ == "__main__":
    setup_08_import_septa_data()
from network_routing import pg_db_connection, GDRIVE_DATA


def setup_03_import_mode_data():
    """
    Import DVRPC's 'Equity Through Access' point dataset
    """
    shp_path = GDRIVE_DATA / "inputs" / "ETA pois" / "eta_essential_services.shp"

    db = pg_db_connection()

    db.import_gis(
        sql_tablename="eta_points", filepath=shp_path, gpd_kwargs={"if_exists": "replace"}
    )

    # Generate a cut of the ETA points for each of the nine counties

    for county_name in db.query_as_list_of_singletons(
        "select distinct co_name from regional_counties"
    ):
        query = f"""
            select
                uid as eta_uid,
                name, type, geom
            from
                eta_points ep
            where
                st_within(
                    geom,
                    (select st_collect(geom) from regional_counties 
                     where co_name = '{county_name}')
                )
        """

        db.gis_make_geotable_from_query(
            query, f"eta_{county_name.lower()}", geom_type="Point", epsg=26918
        )


if __name__ == "__main__":
    setup_03_import_mode_data()

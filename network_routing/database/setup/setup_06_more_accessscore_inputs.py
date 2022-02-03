from network_routing import pg_db_connection, GDRIVE_DATA


def setup_06_more_accessscore_inputs():
    """
    Import AccessScore POI shapefile from GoogleDrive
    """
    db = pg_db_connection()

    shp_path = GDRIVE_DATA / "inputs/AccessScore pois/AccessScoreStations_062521.shp"

    db.import_gis(
        filepath=shp_path, sql_tablename="access_score_pois", gpd_kwargs={"if_exists": "replace"}
    )

    query = """
        select 
            dvrpc_id,
            src,
            type,
            line,
            station,
            operator,
            geom
        from ridescore_pois
        where dvrpc_id in (
            select distinct dvrpc_id
            from access_score_pois
        )

        union

        select 
            dvrpc_id,
            'final_poi_layer' as src,
            type,
            line,
            station,
            operator,
            geom
        from access_score_pois
    """
    db.gis_make_geotable_from_query(query, "access_score_final_poi_set", "POINT", 26918)


if __name__ == "__main__":
    setup_06_more_accessscore_inputs()

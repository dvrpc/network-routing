from network_routing import pg_db_connection, GDRIVE_SW_GAPS_PROJECT_ROOT


def setup_01_updated_ridescore_inputs():
    """
    Import the updated ridescore inputs showing access points to transit stations
    """

    db = pg_db_connection()

    data_folder = GDRIVE_SW_GAPS_PROJECT_ROOT / "data-to-import"

    # Import shapefiles
    for filename_part in ["sw", "osm"]:
        filepath = data_folder / f"station_pois_for_{filename_part}.shp"

        db.import_gis(
            method="geopandas",
            filepath=filepath,
            sql_tablename=f"ridescore_transit_poi_{filename_part}",
            gpd_kwargs={"if_exists": "replace"},
        )

    # Feature engineering to build a single table with all points combined
    query = """
        with all_geoms as (
            select dvrpc_id, geom, 'rs_osm' as src
            from ridescore_transit_poi_osm 
            
            union
            select dvrpc_id, geom, 'rs_sw' as src
            from ridescore_transit_poi_sw
            
            order by dvrpc_id 
        )
        select
            ag.dvrpc_id ,
            ag.geom as geom,
            ag.src,
            prs.type,
            prs.line,
            prs.station,
            prs.operator
        from
            all_geoms ag
        left join
            passengerrailstations prs
        on prs.dvrpc_id = ag.dvrpc_id
    """
    db.gis_make_geotable_from_query(query, "ridescore_pois", "POINT", 26918)


if __name__ == "__main__":
    setup_01_updated_ridescore_inputs()

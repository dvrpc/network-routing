from network_routing import pg_db_connection, GDRIVE_DATA


def setup_05_import_mcpc_and_lts_shapefiles():
    """
    Import MCPC and LTS shapefiles from GoogleDrive
    """
    db = pg_db_connection()

    # Import shapefiles from network folder location

    existing_tables = db.tables(spatial_only=True)

    mcpc_folder = GDRIVE_DATA / "inputs/MCPC pois"
    lts_folder = GDRIVE_DATA / "inputs/LTS Base"

    for folder_path in [mcpc_folder, lts_folder]:
        print(f"Folder: {folder_path}")

        for shp in folder_path.rglob("*.shp"):
            sql_tablename = shp.stem.lower()

            if f"public.{sql_tablename}" not in existing_tables:

                print(f"\tShapefile: {shp.stem}")
                db.import_gis(
                    filepath=shp,
                    sql_tablename=sql_tablename,
                    explode=True,
                    gpd_kwargs={"if_exists": "replace"},
                )

    # Use SQL queries to combine individual tables together
    query = """

    with transit_pois as (
            select
                uid as src_id,
                src as category,
                case
                    when stop_name is not null then stop_name
                    when station_na is not null then station_na
                    when stopname is not null then stopname
                    when station is not null then station
                    when description_bsl is not null then description_bsl
                    when route is not null then route
                    when station_id is not null then station_id
                end as poi_name,
                geom
            from
                regional_transit_stops
    ),
    montco as (
        select geom from regional_counties
        where co_name = 'Montgomery'
    )

        select
            s.poi_name,
            s.category,
            s.src_id,
            s.geom
        from transit_pois s, montco m
        where st_within(s.geom, m.geom)

    union 
        select
            name as poi_name,
            'Libraries' as category,
            uid as src_id,
            st_transform(geom, 26918) as geom
        from montgomery_county_libraries

        UNION

        select
            name as poi_name,
            'Municipal Buildings' as category,
            uid as src_id,
            st_transform(geom, 26918) as geom
        from montgomery_county_municipal_buildings

        union

        select
            name as poi_name,
            concat(type, ' School') as category,
            uid as src_id,
            st_transform(geom, 26918) as geom
        from montgomery_county_schools
        where type != 'Charter'

        union

        select
            name as poi_name,
            type as category,
            uid as src_id,
            st_transform(geom, 26918) as geom
        from eta_montgomery em
        where type not in ('School - Private', 'School - Public')

        UNION

        select
            name as poi_name,
            'Shopping Centers' as category,
            uid as src_id,
            st_transform(
                (st_dumppoints(geom)).geom,
                26918
            )
        from montgomery_county_shopping_centers

        UNION

        select
            name as poi_name,
            'Parks' as category,
            uid as src_id,
            st_transform(
                (st_dumppoints(geom)).geom,
                26918
            )
        from montgomery_county_parks

    """

    db.gis_make_geotable_from_query(query, "mcpc_combined_pois", "POINT", 26918)

    db.execute("alter table mcpc_combined_pois add column poi_uid int;")

    db.execute(
        """
        update mcpc_combined_pois
        set poi_uid = uid
        where category not in ('Shopping Centers', 'Parks')
    """
    )

    db.execute(
        """
        update mcpc_combined_pois
        set poi_uid = src_id + (
            select max(poi_uid) + 1 as num
            from mcpc_combined_pois
        )
        where category  = 'Shopping Centers'
    """
    )

    db.execute(
        """
        update mcpc_combined_pois
        set poi_uid = src_id + (
            select max(poi_uid) + 1 as num
            from mcpc_combined_pois
        )
        where category  = 'Parks'
    """
    )

    db.execute(
        """
    delete from mcpc_combined_pois 
    where not st_within(
                geom, 
                (select geom from regional_counties where co_name = 'Montgomery')
    )
    """
    )

    query = """
    select * from mcpc_combined_pois
    where category like '%%chool%%'
    """
    db.gis_make_geotable_from_query(query, "mcpc_school_pois", "POINT", 26918)


if __name__ == "__main__":
    setup_05_import_mcpc_and_lts_shapefiles()

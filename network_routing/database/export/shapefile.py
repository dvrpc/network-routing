from network_routing import FOLDER_DATA_PRODUCTS, pg_db_connection


def export_data_for_single_muni(muni_name: str) -> None:
    """
    Export a shapefile with the centerline classification
    results for a single municipality. Uses a 1-mile buffer to
    over-select for cartographic purposes (1 mile = 1609.34 meters)
    """
    db = pg_db_connection()

    output_folder = FOLDER_DATA_PRODUCTS / muni_name

    # Make sure the folder exists
    output_folder.mkdir(parents=True, exist_ok=True)

    all_queries = {
        "centerline_coverage": f"""
            select
                osmid, name, highway, oneway, hwy_tag,
                sidewalk, st_length(geom) as shape_len,
                (sidewalk / 2 / st_length(geom)) as sw_ratio,
                CASE WHEN (sidewalk / 2 / st_length(geom)) <= 0.45
                        THEN 'red'
                    WHEN (sidewalk / 2 / st_length(geom)) < 0.82
                        THEN 'orange'
                    ELSE 'green' END AS color,
                geom
            from osm_edges_drive
            where st_dwithin(geom, 
                (select geom from municipalboundaries m 
                where mun_name LIKE '%%{muni_name}%%'),
                1609.34
            )
            and hwy_tag != 'motorway'
            """,
    }

    for output_type in all_queries:

        query = all_queries[output_type]

        output_path = output_folder / f"{muni_name.replace(' ', '_')}_{output_type}.shp"

        db.export_gis(table_or_sql=query, filepath=output_path, filetype="shp")


def export_shapefiles_for_downstream_ridescore():
    db = pg_db_connection()

    output_folder = FOLDER_DATA_PRODUCTS / "islands-and-hulls"

    tables_to_export = [
        "data_viz.islands",
        "data_viz.island_hulls",
    ]

    for tbl in tables_to_export:

        schema, tablename = tbl.split(".")

        db.export_shapefile(tablename, output_folder, schema=schema)


def export_shapefiles_for_editing():
    """
    Export a set of shapefiles that the Bike/Ped/Transit team will edit
    """
    db = pg_db_connection()

    output_folder = FOLDER_DATA_PRODUCTS / "manual_edits"

    tables_to_export = [
        "data_viz.sidewalkscore",
        "data_viz.ridescore_isos",
        "rs_osm.osm_results",
        "rs_sw.sw_results",
        "public.osm_edges_drive",
    ]

    for tbl in tables_to_export:
        db.export_gis(filepath=output_folder, table_or_sql=tbl)

    # Export the QAQC tables so their names don't clash
    gdf = db.gdf("SELECT * FROM rs_osm.qaqc_node_match")
    output_path = output_folder / "osm_qaqc.shp"
    gdf.to_file(output_path)

    gdf = db.gdf("SELECT * FROM rs_sw.qaqc_node_match")
    output_path = output_folder / "sw_qaqc.shp"
    gdf.to_file(output_path)


def export_shapefile_for_rmms():
    """
    Export data for the consultant team working on the
    Racial Minority Mobility Choices study
    """
    db = pg_db_connection()

    output_folder = FOLDER_DATA_PRODUCTS / "rmmc-study"
    filepath = output_folder / "walktime_to_transit.geojson"

    cols = db.columns("sw_defaults.regional_transit_stops_results")

    n1_cols = [x for x in cols if "n_1_" in x]

    query = (
        "select uid, geom, "
        + ", ".join(n1_cols)
        + " from sw_defaults.regional_transit_stops_results"
    )
    print(query)
    gdf = db.gdf(query)

    gdf.to_file(filepath, driver="GeoJSON")


if __name__ == "__main__":
    export_shapefile_for_rmms()

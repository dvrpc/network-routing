from network_routing import db_connection, FOLDER_DATA_PRODUCTS


def export_shapefiles_for_downstream_ridescore():
    db = db_connection()

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
    db = db_connection()

    output_folder = FOLDER_DATA_PRODUCTS / "manual_edits"

    tables_to_export = [
        "data_viz.sidewalkscore",
        "data_viz.ridescore_isos",
        "rs_osm.osm_results",
        "rs_sw.sw_results",
        "public.osm_edges_drive",
    ]

    for tbl in tables_to_export:

        schema, tablename = tbl.split(".")

        db.export_shapefile(tablename, output_folder, schema=schema)

    # Export the QAQC tables so their names don't clash
    gdf = db.query_as_geo_df("SELECT * FROM rs_osm.qaqc_node_match")
    output_path = output_folder / "osm_qaqc.shp"
    gdf.to_file(output_path)

    gdf = db.query_as_geo_df("SELECT * FROM rs_sw.qaqc_node_match")
    output_path = output_folder / "sw_qaqc.shp"
    gdf.to_file(output_path)

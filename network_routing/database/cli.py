import click

from network_routing import db_connection, FOLDER_DATA_PRODUCTS
from network_routing.database.setup.nodes import generate_nodes
from network_routing.database.export.vector_tiles import (
    make_vector_tiles as _make_vector_tiles,
)
from network_routing.database.export.geojson import (
    export_gap_webmap_data,
    export_ridescore_webmap_data,
)
from network_routing.database.setup.setup_00_initial import setup_00_initial
from network_routing.database.setup.setup_01_updated_ridescore_inputs import (
    setup_01_updated_ridescore_inputs,
)


@click.group()
def main():
    """The command 'db' is used to run data import & export processes"""
    pass


@click.command()
def build_initial():
    """Roll a brand-new database for with the latest-and-greatest data"""
    db = db_connection()

    setup_00_initial(db)


@click.command()
@click.argument("patch_number", type=int)
def build_secondary(patch_number):

    patches = {
        1: setup_01_updated_ridescore_inputs,
    }

    if patch_number not in patches:
        print(f"Patch #{patch_number} does not exist")

    else:
        print(f"Running patch #{patch_number}")
        patch = patches[patch_number]
        patch()


@click.command()
def make_nodes_for_edges():
    """ Generate topologically-sound nodes for the OPENSTREETMAP centerlines & SIDEWALK lines """

    db = db_connection()

    print("Generating OSM nodes")
    edge_table = "osm_edges_all"
    geotable_kwargs = {
        "new_table_name": "nodes_for_osm",
        "geom_type": "Point",
        "epsg": 26918,
        "uid_col": "node_id",
    }
    generate_nodes(db, edge_table, "public", geotable_kwargs)

    print("Generating SIDEWALK nodes")
    edge_table = "pedestriannetwork_lines"
    geotable_kwargs = {
        "new_table_name": "nodes_for_sidewalks",
        "geom_type": "Point",
        "epsg": 26918,
        "uid_col": "sw_node_id",
    }
    generate_nodes(db, edge_table, "public", geotable_kwargs)


@click.command()
@click.argument("data_group_name")
def export_geojson(data_group_name):
    """Save RIDESCORE .geojson files to be tiled for webmaps"""

    db = db_connection()

    if data_group_name == "ridescore":
        export_ridescore_webmap_data(db)

    elif data_group_name == "gaps":
        export_gap_webmap_data(db)

    else:
        print(f"Group named: '{data_group_name}' does not exist")


@click.command()
@click.argument("filename")
def make_vector_tiles(filename):
    """Turn GeoJSON files into .mbtiles format"""
    _make_vector_tiles(FOLDER_DATA_PRODUCTS, filename)


@click.command()
def export_shps_for_manual_edits():
    """Export data necessary for manual station edits"""

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


all_commands = [
    build_initial,
    build_secondary,
    make_nodes_for_edges,
    export_geojson,
    make_vector_tiles,
    export_shps_for_manual_edits,
]

for cmd in all_commands:
    main.add_command(cmd)


if __name__ == "__main__":
    pass

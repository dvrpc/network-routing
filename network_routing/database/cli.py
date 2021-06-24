"""
`db`
----

`db` is the command-line-interface for the `network_routing.database` module.

Examples:

    Create the database, load secondary layers, and generate new features:
    ```shell
    > db build-initial
    > db build-secondary 1
    > db build-secondary 2
    > db make-nodes-for-edges
    ```

    To see all available commands, run `db --help`

    ```shell
    > db --help

    Usage: db [OPTIONS] COMMAND [ARGS]...

    The command 'db' is used to run data import & export processes

    Options:
    --help  Show this message and exit.

    Commands:
    build-initial         Roll a brand-new database for with the...
    build-secondary       Update the db as defined by PATCH NUMBER
    export-geojson        Save a group of .geojson files to be tiled for...
    export-shapefiles     Export a set of shapefiles identified by EXPORT_NAME
    make-nodes-for-edges  Generate topologically-sound nodes for the...
    make-vector-tiles     Turn GeoJSON files into .mbtiles format
    ```
"""

import click

from network_routing import db_connection, FOLDER_DATA_PRODUCTS
from network_routing.database.setup.make_nodes import generate_nodes
from network_routing.database.export.vector_tiles import (
    make_vector_tiles as _make_vector_tiles,
)
from network_routing.database.export.geojson import (
    export_gap_webmap_data,
    export_ridescore_webmap_data,
    export_county_specific_data,
)
from network_routing.database.setup.setup_00_initial import setup_00_initial
from network_routing.database.setup.setup_01_updated_ridescore_inputs import (
    setup_01_updated_ridescore_inputs,
)
from network_routing.database.setup.setup_02_osm_drive import setup_02_import_osm_drive_network
from network_routing.database.setup.step_03_more_inputs import setup_03_import_mode_data
from network_routing.database.export.shapefile import (
    export_shapefiles_for_editing,
    export_shapefiles_for_downstream_ridescore,
    export_data_for_single_muni,
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
    """Update the db as defined by PATCH NUMBER """

    patches = {
        1: setup_01_updated_ridescore_inputs,
        2: setup_02_import_osm_drive_network,
        3: setup_03_import_mode_data,
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

    _shared_kwargs = {
        "geom_type": "Point",
        "epsg": 26918,
    }

    tables_to_make_nodes_from = {
        "osm_edges_all": {
            "new_table_name": "nodes_for_osm_all",
            "uid_col": "node_id",
        },
        "osm_edges_drive": {
            "new_table_name": "nodes_for_osm_drive",
            "uid_col": "node_id",
        },
        "pedestriannetwork_lines": {
            "new_table_name": "nodes_for_sidewalks",
            "uid_col": "sw_node_id",
        },
    }

    for tablename, kwargs in tables_to_make_nodes_from.items():
        print(f"Generating nodes for: {tablename}")
        kwargs.update(_shared_kwargs)
        generate_nodes(db, tablename, "public", kwargs)


@click.command()
@click.argument("data_group_name")
def export_geojson(data_group_name):
    """Save a group of .geojson files to be tiled for webmaps"""

    db = db_connection()

    exporters = {
        "ridescore": export_ridescore_webmap_data,
        "gaps": export_gap_webmap_data,
        "mcpc": export_county_specific_data,
    }

    if data_group_name not in exporters:
        print(f"GeoJSON export process named '{data_group_name}' does not exist. Options include:")
        for k in exporters.keys():
            print(f"\t -> {k}")

    else:
        func = exporters[data_group_name]
        func(db)


@click.command()
@click.argument("folder")
@click.argument("filename")
def make_vector_tiles(folder, filename):
    """Turn GeoJSON files into .mbtiles format"""
    folder_path = FOLDER_DATA_PRODUCTS / folder
    _make_vector_tiles(folder_path, filename)


@click.command()
@click.argument("export_name")
def export_shapefiles(export_name):
    """Export a set of shapefiles identified by EXPORT_NAME"""

    exporters = {
        "manual_edits": export_shapefiles_for_editing,
        "ridescore_downstream_analysis": export_shapefiles_for_downstream_ridescore,
    }

    if export_name not in exporters:
        print(f"Export process named '{export_name}' does not exist. Options include:")
        for k in exporters.keys():
            print(f"\t -> {k}")

    else:
        func = exporters[export_name]
        func()


@click.command()
@click.argument("muni_name")
def export_muni_shapefiles(muni_name):
    """
    Export shapefile(s) clipped to a single municipality
    """

    export_data_for_single_muni(muni_name)


_all_commands = [
    build_initial,
    build_secondary,
    make_nodes_for_edges,
    export_geojson,
    make_vector_tiles,
    export_shapefiles,
    export_muni_shapefiles,
]

for cmd in _all_commands:
    main.add_command(cmd)


if __name__ == "__main__":
    pass

"""
`gaps`
------

`gaps` is the command-line-interface for the `network_routing.gaps` module.

Examples:
    Classify the OSM centerlines by sidewalk coverage

    ```shell
    > gaps classify-osm-sw-coverage
    ```

    You can also see a list of all available configurations by running `gaps --help`

    ```shell
    > gaps --help

    Usage: gaps [OPTIONS] COMMAND [ARGS]...

    The command 'gaps' is used for segment-specific gap analyses

    Options:
    --help  Show this message and exit.

    Commands:
    classify-osm-sw-coverage  Classify OSM w/ length of parallel sidewalks
    identify-islands          Join intersecting sidewalks to create 'islands'
    isochrones                Turn access results into isochrone polygons
    scrub-osm-tags            Clean 'highway' tags in the OSM data
    sidewalkscore             Calculate the SidewalkScore for each rail stop
    ```

"""

import click

from network_routing import db_connection, pg_db_connection

from network_routing.gaps.segments.centerline_sidewalk_coverage import classify_centerlines
from network_routing.gaps.segments.generate_islands import generate_islands

from network_routing.gaps.data_viz.handle_osm_tags import scrub_osm_tags as _scrub_osm_tags
from network_routing.gaps.data_viz.ridescore_isochrones import (
    generate_isochrones,
    calculate_sidewalkscore,
)
from network_routing.gaps.data_viz.eta_isochrones import IsochroneGenerator


@click.group()
def main():
    "The command 'gaps' is used for segment-specific gap analyses"
    pass


@click.command()
@click.argument("schema", default="public")
def classify_osm_sw_coverage(schema: str):
    """ Classify OSM w/ length of parallel sidewalks """

    db = db_connection()

    classify_centerlines(db, schema, "osm_edges_drive")


@click.command()
@click.option("-s", "--schema")
def identify_islands(schema: str):
    """ Join intersecting sidewalks to create 'islands' """

    db = db_connection()

    print("schema: ", schema)

    generate_islands(db, schema)


@click.command()
def isochrones_accessscore():
    """
    Make 'Access Score' isos & POIs with stats
    """

    db = db_connection()

    generate_isochrones(db)

    query = """
        select
            st_centroid(st_collect(geom)) as geom,
            type, line, station, operator, dvrpc_id as poi_uid
        from ridescore_pois
        group by type, line, station, operator, dvrpc_id 
        order by dvrpc_id
    """

    calculate_sidewalkscore(db, query)


@click.command()
@click.argument("county", default="montgomery")
def isochrones_eta(county: str):
    """
    Make 'ETA' isos & POIs with stats

    """
    db = pg_db_connection()

    county = county.lower()

    args = {
        "db": db,
        "poi_table": f"eta_{county}",
        "poi_col": "eta_uid",
        "network_a_edges": "pedestriannetwork_lines",
        "network_a_nodes": "nodes_for_sidewalks",
        "network_a_node_id_col": "sw_node_id",
        "network_b_edges": "osm_edges_all",
        "network_b_nodes": "nodes_for_osm_all",
        "network_b_node_id_col": "node_id",
        "data_dir": "./data",
    }

    i = IsochroneGenerator(**args)
    i.save_isos_to_db()
    i.save_pois_with_iso_stats_to_db()


@click.command()
def scrub_osm_tags():
    """ Clean 'highway' tags in the OSM data """

    db = db_connection()

    _scrub_osm_tags(db)


_all_commands = [
    classify_osm_sw_coverage,
    identify_islands,
    scrub_osm_tags,
    isochrones_accessscore,
    isochrones_eta,
]

for cmd in _all_commands:
    main.add_command(cmd)

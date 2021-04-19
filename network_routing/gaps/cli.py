import click

from network_routing import db_connection

from network_routing import db_connection
from network_routing.gaps.segments.centerline_sidewalk_coverage import classify_centerlines
from network_routing.gaps.segments.generate_islands import generate_islands

from network_routing.gaps.data_viz.handle_osm_tags import scrub_osm_tags as _scrub_osm_tags
from network_routing.gaps.data_viz.ridescore_isochrones import (
    generate_isochrones,
    calculate_sidewalkscore,
)


@click.group()
def main():
    "The command 'gaps' is used for the Sidewalk Gap Analysis project."
    pass


@click.command()
@click.argument("schema", default="public")
def classify_osm_sw_coverage(schema: str):
    """ Classify OSM w/ length of parallel sidewalks """

    db = db_connection()

    classify_centerlines(db, schema, "osm_edges_all")


@click.command()
@click.option("-s", "--schema")
def identify_islands(schema: str):
    """ Join intersecting sidewalks to create 'islands' """

    db = db_connection()

    print("schema: ", schema)

    generate_islands(db, schema)


@click.command()
def isochrones():
    """Turn access results into isochrone polygons"""

    db = db_connection()

    generate_isochrones(db)


@click.command()
def sidewalkscore():
    """Calculate the SidewalkScore for each rail stop"""

    db = db_connection()

    calculate_sidewalkscore(db)


@click.command()
def scrub_osm_tags():
    """ Clean 'highway' tags in the OSM data """

    db = db_connection()

    _scrub_osm_tags(db)


all_commands = [
    classify_osm_sw_coverage,
    identify_islands,
    scrub_osm_tags,
    isochrones,
    sidewalkscore,
]

for cmd in all_commands:
    main.add_command(cmd)

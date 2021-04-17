import click

from network_routing import db_connection

from network_routing.gaps.segments import commands as segment_commands
from network_routing.gaps.data_viz import commands as viz_commands
from network_routing.gaps.extract_data import commands as extraction_commands


@click.group()
def main():
    "The command 'sidewalk' is used for the Sidewalk Gap Analysis project."
    pass


all_commands = [
    extraction_commands.clip_data,
    segment_commands.analyze_segments,
    segment_commands.identify_islands,
    viz_commands.combine_centerlines,
    viz_commands.scrub_osm_tags,
    viz_commands.combine_transit_results,
    viz_commands.isochrones,
    viz_commands.sidewalkscore,
]

for cmd in all_commands:
    main.add_command(cmd)

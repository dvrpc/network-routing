import click

from sidewalk_gaps.db_setup import commands as db_setup_commands
from sidewalk_gaps.extract_data import commands as data_extraction_commands
from sidewalk_gaps.accessibility import commands as accessibility_commands
from sidewalk_gaps.segments import commands as segment_commands

@click.group()
def main():
    pass


main.add_command(db_setup_commands.db_setup)
main.add_command(db_setup_commands.db_load)
main.add_command(db_setup_commands.db_freeze)
main.add_command(db_setup_commands.generate_nodes)
main.add_command(data_extraction_commands.clip_data)
main.add_command(segment_commands.analyze_segments)
main.add_command(segment_commands.identify_islands)
main.add_command(accessibility_commands.analyze_network)

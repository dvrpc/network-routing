import click

from network_routing.improvements.generate_segments import draw_missing_network_links
from network_routing.improvements.feature_engineering import feature_engineering
from network_routing.improvements.network_node import reconnect_nodes


@click.group()
def main():
    "The command 'improvements' is used to generate and analyze potential sidewalk improvement projects"
    pass


_all_commands = [draw_missing_network_links, feature_engineering, reconnect_nodes]

for cmd in _all_commands:
    main.add_command(cmd)

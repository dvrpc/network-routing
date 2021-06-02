import click

from network_routing import pg_db_connection

from network_routing.improvements.generate_segments import (
    generate_missing_network as _generate_missing_network,
)


@click.group()
def main():
    "The command 'improvements' is used for segment-specific gap analyses"
    pass


@click.command()
def generate_missing_network():
    """Create a full sidewalk network on streets lacking sidewalks on both sides"""

    db = pg_db_connection()

    _generate_missing_network(db)


_all_commands = [
    generate_missing_network,
]

for cmd in _all_commands:
    main.add_command(cmd)

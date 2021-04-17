import click

from helpers import RoutableNetwork, db_connection


@click.command()
@click.argument("schema")
def analyze_network(schema: str):
    """Run the sidewalk network analysis with Pandana"""

    db = db_connection()

    # Note: the default inputs for RouteableNetwork
    # are tailored to this analysis
    arguments = {
        "output_schema": f"gaps_{schema}",
        "max_minutes": 180,
    }

    _ = RoutableNetwork(db, schema, **arguments)

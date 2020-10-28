
import click

from postgis_helpers import PostgreSQL

from helpers import RoutableNetwork, db_connection


@click.command()
@click.argument("schema")
def analyze_network(schema: str):
    """Run the sidewalk network analysis with Pandana"""

    db = db_connection()

    # note: the default inputs for RouteableNetwork 
    # are tailored to this analysis
    network = RoutableNetwork(db, schema, output_schema=f"gaps_{schema}")

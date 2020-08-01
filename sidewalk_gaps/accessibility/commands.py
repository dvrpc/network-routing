
import click

from postgis_helpers import PostgreSQL

from sidewalk_gaps import CREDENTIALS

from .network_analysis import SidewalkNetwork


@click.command()
@click.argument("schema")
@click.option(
    "--database", "-d",
    help="Name of the local database",
    default="sidewalk_gaps",
)
@click.option(
    "--speed", "-s",
    help="Speed of pedestrians in miles per hour",
    default="sidewalk_gaps",
)
def analyze(schema: str,
            database: str,
            speed: str):
    """Run the sidewalk analysis"""

    try:
        speed = float(speed)
    except ValueError:
        speed = None

    db = PostgreSQL(database, verbosity="minimal", **CREDENTIALS["localhost"])

    net = SidewalkNetwork(db, schema)

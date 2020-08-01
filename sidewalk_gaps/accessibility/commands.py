
import click

from postgis_helpers import PostgreSQL

from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME

from .network_analysis import SidewalkNetwork


@click.command()
@click.argument("schema")
@click.option(
    "--database", "-d",
    help=f"Name of the local database. Default = {PROJECT_DB_NAME}",
    default=PROJECT_DB_NAME,
)
@click.option(
    "--speed", "-s",
    help="Speed of pedestrians in miles per hour. Default = 2.5",
    default="2.5",
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

    network = SidewalkNetwork(db, schema, walking_mph=speed)

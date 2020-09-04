import click

from postgis_helpers import PostgreSQL

from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME
from .hexagon_summary import hexagon_summary

@click.command()
@click.option(
    "--database", "-d",
    help="Name of the local database",
    default=PROJECT_DB_NAME,
)
def summarize_into_hexagons(database: str):
    """ Classify centerlines w/ length of parallel sidewalks """
    db = PostgreSQL(database, verbosity="minimal", **CREDENTIALS["localhost"])
    hexagon_summary(db)


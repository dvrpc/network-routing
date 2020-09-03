import click

from postgis_helpers import PostgreSQL

from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME
from .centerline_sidewalk_coverage import classify_centerlines


@click.command()
@click.argument("schema")
@click.option(
    "--database", "-d",
    help="Name of the local database",
    default=PROJECT_DB_NAME,
)
def analyze_segments(schema: str, database):
    """ Classify centerline segments with the length of parallel sidewalks """
    db = PostgreSQL(database, verbosity="minimal", **CREDENTIALS["localhost"])
    classify_centerlines(db, schema, "centerlines")

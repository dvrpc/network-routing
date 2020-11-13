import click

from helpers import db_connection
from .hexagon_summary import hexagon_summary, classify_hex_results


@click.command()
def summarize_into_hexagons():
    """ Classify centerlines w/ length of parallel sidewalks """

    db = db_connection()

    hexagon_summary(db)


@click.command()
def classify_hexagons():
    """ Prepare analysis result for bivariate choropleth map """

    db = db_connection()

    classify_hex_results(db)

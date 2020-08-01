import click

from postgis_helpers import PostgreSQL

from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME
from .clip_inputs import clip_inputs

# CLIP SOURCE DATA TO SMALL STUDY AREA
# ------------------------------------


@click.command()
@click.argument("state")
@click.option(
    "--municipality", "-m",
    help="Clip to a municipality",
    default="",
)
@click.option(
    "--buffer", "-b",
    help="Buffer distance in meters",
    default="",
)
@click.option(
    "--database", "-d",
    help="Name of the local database",
    default=PROJECT_DB_NAME,
)
def clip_data(state: str,
              municipality: str,
              buffer: str,
              database):
    """Clip source data down to a single municipality"""

    if municipality == "":
        municipality = None

    try:
        buffer = float(buffer)
    except ValueError:
        buffer = None

    db = PostgreSQL(database, verbosity="minimal", **CREDENTIALS["localhost"])
    clip_inputs(db, state, municipality=municipality, buffer_meters=buffer)

import click

from helpers import db_connection

from .clip_inputs import clip_inputs


# CLIP SOURCE DATA TO SMALL STUDY AREA
# ------------------------------------


@click.command()
@click.argument("state")
@click.option(
    "--municipality",
    "-m",
    help="Clip to a municipality",
    default="",
)
@click.option(
    "--buffer",
    "-b",
    help="Buffer distance in meters",
    default="",
)
def clip_data(state: str, municipality: str, buffer: str):
    """Clip source data down to a single municipality"""

    if municipality == "":
        municipality = None

    try:
        buffer = float(buffer)
    except ValueError:
        buffer = None

    db = db_connection()

    clip_inputs(db, state, municipality=municipality, buffer_meters=buffer)

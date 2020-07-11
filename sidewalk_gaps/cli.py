import click
from pathlib import Path
from typing import Union

from postgis_helpers import PostgreSQL

from sidewalk_gaps.download_data import download_data
from sidewalk_gaps.clip_inputs import clip_inputs
from sidewalk_gaps.network_analysis import SidewalkNetwork


import sidewalk_gaps
from sidewalk_gaps import (
    CREDENTIALS,
    FOLDER_SHP_INPUT,
    FOLDER_DB_BACKUPS,
)


@click.group()
def main():
    """ sidewalk is a command-line utility for the
    sidewalk_gaps project.

    To get more information on a particular command,
    type: sidewalk COMMAND --help
    All available commands are shown below.
    """
    pass


# ROLL THE PROJECT DATABASE
# -------------------------

@main.command()
@click.option(
    "--database", "-d",
    help="Name of the local database",
    default="sidewalk_gaps",
)
@click.option(
    "--folder", "-f",
    help="Folder where input shapefiles are stored",
    default=FOLDER_SHP_INPUT,
)
def create_database(database: str, folder: str):
    """Roll a starter database from DVRPC's production DB"""

    folder = Path(folder)

    db = PostgreSQL(database, verbosity="minimal", **CREDENTIALS["localhost"])

    download_data(db, folder)


# LOAD UP AN ALREADY-CREATED DATABASE
# -----------------------------------

@main.command()
@click.option(
    "--database", "-d",
    help="Name of the local database",
    default="sidewalk_gaps",
)
@click.option(
    "--folder", "-f",
    help="Folder where database backups are stored",
    default=FOLDER_DB_BACKUPS,
)
def load_database(database: PostgreSQL, folder: str):
    """ Load up a .SQL file created by another process """

    folder = Path(folder)

    # Find the one with the highest version tag

    all_db_files = [x for x in folder.rglob("*.sql")]

    max_version = -1
    latest_file = None

    for db_file in all_db_files:
        v_number = db_file.name[:-4].split("_")[-1]

        version = int(v_number[1:])

        if version > max_version:
            max_version = version
            latest_file = db_file

    print(f"Loading db version {max_version} from \n\t-> {latest_file}")

    db = PostgreSQL(database, verbosity="minimal", **CREDENTIALS["localhost"])
    db.db_load_pgdump_file(latest_file)


# CLIP SOURCE DATA TO SMALL STUDY AREA
# ------------------------------------


@main.command()
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
    default="sidewalk_gaps",
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




# EXECUTE THE ANALYSIS
# --------------------


@main.command()
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

import click
from pathlib import Path

from postgis_helpers import PostgreSQL

from sidewalk_gaps import FOLDER_SHP_INPUT, CREDENTIALS, FOLDER_DB_BACKUPS

from .db_setup import create_project_database


@click.command()
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
def db_setup(database: str, folder: str):
    """Roll a starter database from DVRPC's production DB"""

    folder = Path(folder)

    db = PostgreSQL(database, verbosity="minimal", **CREDENTIALS["localhost"])

    create_project_database(db, folder)



# FREEZE A DATABASE
# -----------------

@click.command()
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
def db_freeze(database: PostgreSQL, folder: str):
    """ Export a .SQL file of the database """

    folder = Path(folder)

    db = PostgreSQL(database, verbosity="minimal", **CREDENTIALS["localhost"])

    db.db_export_pgdump_file(folder)


# LOAD UP AN ALREADY-CREATED DATABASE
# -----------------------------------

@click.command()
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
def db_load(database: PostgreSQL, folder: str):
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

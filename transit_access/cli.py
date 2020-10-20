import click

from postgis_helpers import PostgreSQL

from transit_access import GDRIVE_ROOT

from sidewalk_gaps.db_setup.db_setup import import_shapefiles
from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME


@click.group()
def main():
    pass


@click.command()
def import_data():
    """Import RideScore data into the SQL database"""
    db = PostgreSQL(PROJECT_DB_NAME, **CREDENTIALS["localhost"])
    ridescore_inputs = GDRIVE_ROOT / "inputs"
    import_shapefiles(ridescore_inputs, db)


main.add_command(import_data)

if __name__ == "__main__":
    pass

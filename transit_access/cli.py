import click

from postgis_helpers import PostgreSQL

from transit_access import GDRIVE_ROOT, db

from sidewalk_gaps.db_setup.db_setup import import_shapefiles

from transit_access.ridescore_isochrones import calculate_sidewalk_walksheds, generate_isochrones


@click.group()
def main():
    "The command 'transit' is used for the RideScore project update."
    pass


@click.command()
def import_data():
    """Import RideScore data into the SQL database"""
    ridescore_inputs = GDRIVE_ROOT / "inputs"
    import_shapefiles(ridescore_inputs, db)


@click.command()
def data_engineering():
    """Massage the data to prepare for analysis"""

    for schema, state_name in [("nj", "New Jersey"), ("pa", "Pennsylvania")]:
        query = f"""
            select * from passengerrailstations p
            where
                st_within(
                    geom,
                    (select st_collect(geom) from regional_counties
                        where state_name = '{state_name}')
                )
        """
        db.make_geotable_from_query(
            query,
            "ridescore_stations",
            "POINT",
            26918,
            schema=schema
        )


@click.command()
def calculate_sidewalks():
    """Analyze sidewalk network distance around each rail stop """
    calculate_sidewalk_walksheds()


@click.command()
def isochrones():
    """Turn access results into isochrone polygons"""
    generate_isochrones()


all_commands = [import_data, data_engineering, calculate_sidewalks, isochrones]

for cmd in all_commands:
    main.add_command(cmd)


if __name__ == "__main__":
    pass

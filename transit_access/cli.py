import click

# from postgis_helpers import PostgreSQL

from helpers import db_connection, generate_nodes

from transit_access.ridescore_isochrones import (
    calculate_sidewalk_walksheds,
    generate_isochrones
)


@click.group()
def main():
    "The command 'transit' is used for the RideScore project update."
    pass


@click.command()
def data_engineering():
    """Massage the data to prepare for analysis"""

    db = db_connection()

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

    db = db_connection()
    
    calculate_sidewalk_walksheds(db)


@click.command()
def isochrones():
    """Turn access results into isochrone polygons"""

    db = db_connection()

    generate_isochrones(db)


@click.command()
def make_nodes():
    """ Generate topologically-sound nodes for the centerlines """

    db = db_connection()

    kwargs = {
        "new_table_name": "nodes_for_osm",
        "geom_type": "Point",
        "epsg": 26918,
        "uid_col": "node_id",
    }

    edge_table = "osm_edges"

    print(f"Generating nodes for {edge_table}")
    generate_nodes(db, edge_table, "public", kwargs)


all_commands = [
    data_engineering,
    calculate_sidewalks,
    isochrones,
    make_nodes
]

for cmd in all_commands:
    main.add_command(cmd)


if __name__ == "__main__":
    pass

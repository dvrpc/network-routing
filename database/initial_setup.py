import os
import platform
import socket

import postgis_helpers as pGIS
from postgis_helpers import PostgreSQL
from philly_transit_data import TransitData


def import_production_sql_data(remote_db: PostgreSQL, local_db: PostgreSQL):
    """
    Copy data from DVRPC's production SQL database to a
    SQL database on localhost.

    Note - this connection will only work within the firewall.
    """

    data_to_download = [
        ("transportation", ["pedestriannetwork_lines",
                            "pedestriannetwork_points",
                            "passengerrailstations",
                            "transitparkingfacilities",
                            ]),

        ("structure", ["points_of_interest"]),

        ("boundaries", ["municipalboundaries"]),
    ]

    for schema, table_list in data_to_download:

        for table_name in table_list:

            # Extract the data from the remote database
            # and rename the geom column
            query = f"SELECT * FROM {schema}.{table_name};"
            gdf = remote_db.query_as_geo_df(query, geom_col="shape")
            gdf = gdf.rename(
                columns={"shape": "geometry"}
            ).set_geometry("geometry")

            # Check if we have multipart geometries.
            # If so, explode them (but keep the index)
            multipart = False
            for geom_type in gdf.geom_type.unique():
                if "Multi" in geom_type:
                    multipart = True

            if multipart:
                print(f"EXPLODING {table_name}")
                gdf = gdf.explode()
                gdf['explode'] = gdf.index
                gdf = gdf.reset_index()

            # Save to the local database
            local_db.import_geodataframe(gdf, table_name.lower())


def load_helper_functions(db: PostgreSQL):
    """ Add a SQL function to get a median() """

    db.execute("""
        DROP FUNCTION IF EXISTS _final_median(anyarray);
        CREATE FUNCTION _final_median(anyarray) RETURNS float8 AS $$
        WITH q AS
        (
            SELECT val
            FROM unnest($1) val
            WHERE VAL IS NOT NULL
            ORDER BY 1
        ),
        cnt AS
        (
            SELECT COUNT(*) as c FROM q
        )
        SELECT AVG(val)::float8
        FROM
        (
            SELECT val FROM q
            LIMIT  2 - MOD((SELECT c FROM cnt), 2)
            OFFSET GREATEST(CEIL((SELECT c FROM cnt) / 2.0) - 1,0)
        ) q2;
        $$ LANGUAGE sql IMMUTABLE;

        CREATE AGGREGATE median(anyelement) (
        SFUNC=array_append,
        STYPE=anyarray,
        FINALFUNC=_final_median,
        INITCOND='{}'
        );
    """)


def create_new_geodata(db: PostgreSQL):
    """ 1) Merge DVRPC municipalities into counties
        2) Filter POIs to those within DVRPC counties
    """

    pa_counties = """
        ('Bucks', 'Chester', 'Delaware', 'Montgomery', 'Philadelphia')
    """
    nj_counties = "('Burlington', 'Camden', 'Gloucester', 'Mercer')"

    # Add regional county data
    regional_counties = f"""
        select co_name, state_name, (st_dump(st_union(geom))).geom
        from public.municipalboundaries m
        where (co_name in {pa_counties} and state_name ='Pennsylvania')
            or
            (co_name in {nj_counties} and state_name = 'New Jersey')
        group by co_name, state_name
    """
    db.make_geotable_from_query(
        regional_counties,
        "regional_counties",
        "Polygon",
        26918,
        schema="public"
    )

    # Clip POIs to those inside DVRPC's region
    regional_pois = """
        select * from public.points_of_interest
        where st_intersects(geom, (select st_collect(geom)
                                   from public.regional_counties))
    """
    db.make_geotable_from_query(
        regional_pois,
        "regional_pois",
        "Point",
        26918,
        schema="public"
    )


def create_project_database(local_db: PostgreSQL):
    """ Batch execute the entire process """

    if platform.system() in ["Linux", "Windows"] \
       and "dvrpc.org" in socket.getfqdn():

        dvrpc_credentials = pGIS.configurations()["dvrpc_gis"]
        remote_db = PostgreSQL("gis", **dvrpc_credentials)

        # 1) Copy SQL data from production database
        import_production_sql_data(remote_db, local_db)

        # 2) Load the MEDIAN() function into SQL
        load_helper_functions(local_db)

        # 3) Create new layers using what's already been imported
        create_new_geodata(local_db)

        # 4) Import all regional transit stops
        transit_data = TransitData()
        stops, lines = transit_data.all_spatial_data()
        local_db.import_geodataframe(stops, "regional_transit_stops")

        # 5) Import OSM data for the entire region
        os.system("db-import osm")

    else:
        print("""
            -> ! DB setup can only be executed from a DVRPC workstation!!!
        """)


if __name__ == "__main__":

    from helpers import db_connection

    db = db_connection()

    create_project_database(db)

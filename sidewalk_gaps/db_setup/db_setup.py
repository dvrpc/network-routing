"""
Summary of ``download_data.py``
-------------------------------

This script copies the sidewalk data from DVRPC's production database.

It will create a database on localhost, and also save a pg_dump snapshot.

Assumptions
-----------
    - You've executed "pGIS init" to generate the db connection file
    - You've added an entry with credentials for "dvrpc_gis"

Usage
-----

    In [1]: import sidewalk_gaps

    In [2]: from postgis_helpers import PostgreSQL

    In [3]: from sidewalk_gaps.download_data import download_data

    In [4]: db = PostgreSQL('my_db_name', **sidewalk_gaps.CREDENTIALS["localhost"])

    In [5]: download_data(db, sidewalk_gaps.FOLDER_SHP_INPUT)


"""
from pathlib import Path
import platform
import socket

import postgis_helpers as pGIS
from postgis_helpers import PostgreSQL


def import_production_sql_data(remote_db: PostgreSQL, local_db: PostgreSQL):
    """
    Copy data from DVRPC's production SQL database to a SQL database on localhost.

    Note - this connection will only work within the firewall.
    """

    data_to_download = [
        ("transportation", ["pedestriannetwork_lines",
                            "pedestriannetwork_points",
                            "pa_centerline",
                            ]),

        ("structure", ["points_of_interest"]),

        ("boundaries", ["municipalboundaries"]),
    ]

    for schema, table_list in data_to_download:

        for table_name in table_list:

            # Extract the data from the remote database and rename the geom column
            query = f"SELECT * FROM {schema}.{table_name};"
            gdf = remote_db.query_as_geo_df(query, geom_col="shape")
            gdf = gdf.rename(columns={"shape": "geometry"}).set_geometry("geometry")

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
            local_db.import_geodataframe(gdf, table_name)


def import_shapefiles(folder: Path, db: PostgreSQL):
    """ Import all shapefiles within the folder into SQL.
        This includes:
            - nj_centerline.shp
    """

    for shp_path in folder.rglob("*.shp"):

        pg_name = shp_path.name[:-4].replace(" ", "_").lower()

        db.import_geodata(pg_name, shp_path, if_exists="replace")


def load_helper_functions(db: PostgreSQL):
    """ Add a SQL function to get a median() """

    db.execute("""
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

    pa_counties = "('Bucks', 'Chester', 'Delaware', 'Montgomery', 'Philadelphia')"
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
        where st_intersects(geom, (select st_collect(geom) from public.regional_counties))
    """
    db.make_geotable_from_query(
        regional_pois,
        "regional_pois",
        "Point",
        26918,
        schema="public"
    )


def create_project_database(local_db: PostgreSQL, shp_folder: Path):
    """ Batch execute the whole process:
            1) copy SQL data
            2) import shapefiles
            3) load a median() function
            4) make some helper GIS data
            5) save pg_dump of database
    """

    if platform.system() in ["Linux", "Windows"] \
       and "dvrpc.org" in socket.getfqdn():

        dvrpc_credentials = pGIS.configurations()["dvrpc_gis"]
        remote_db = PostgreSQL("gis", **dvrpc_credentials)

        import_production_sql_data(remote_db, local_db)
        import_shapefiles(shp_folder, local_db)
        load_helper_functions(local_db)
        create_new_geodata(local_db)

    else:
        print("\n-> !!!Initial DB setup can only be executed from a DVRPC workstation!!!")


if __name__ == "__main__":

    from sidewalk_gaps import CREDENTIALS, FOLDER_SHP_INPUT

    db = PostgreSQL('my_db_name', **CREDENTIALS["localhost"])

    create_project_database(db, FOLDER_SHP_INPUT)

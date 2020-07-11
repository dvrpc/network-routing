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

    # # Custom query is needed for nj_centerline
    # nj_centerline_query = """
    #     SELECT *, (ST_DUMP(shape)).geom
    #     FROM transportation.nj_centerline
    # """

    # nj_gdf = remote_db.query_as_geo_df(nj_centerline_query)

    # # Remove 'nan's
    # for idx, row in nj_gdf.iterrows():
    #     geom_txt = str(row["geom"])
    #     if "nan" in geom_txt:
    #         nj_gdf = nj_gdf.drop(idx)

    # local_db.import_geodataframe(nj_gdf, "nj_centerlines")

    # if "nj_centerline" not in local_db.all_spatial_tables_as_dict():
    #     print("ERROR! nj_centerline didn't make it! ")


def import_shapefiles(folder: Path, db: PostgreSQL):
    """ Import all shapefiles within the folder into SQL. """

    for shp_path in folder.rglob("*.shp"):

        pg_name = shp_path.name[:-4].replace(" ", "_").lower()

        db.import_geodata(pg_name, shp_path, if_exists="replace")


def download_data(local_db: PostgreSQL, shp_folder: Path):
    """ Batch execute the whole process:
            1) copy SQL data
            2) import shapefiles
            3) save pg_dump of database
    """

    if platform.system() in ["Linux", "Windows"] \
       and "dvrpc.org" in socket.getfqdn():

        dvrpc_credentials = pGIS.configurations()["dvrpc_gis"]
        remote_db = PostgreSQL("gis", **dvrpc_credentials)

        import_production_sql_data(remote_db, local_db)
        import_shapefiles(shp_folder, local_db)

        # Add the median function to the database
        median_sql_function = """
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
        """
        local_db.execute(median_sql_function)

        # Add regional county data
        regional_counties = """
            select co_name, state_name, (st_dump(st_union(geom))).geom
            from public.municipalboundaries m 
            where (co_name in ('Bucks', 'Chester', 'Delaware', 'Montgomery', 'Philadelphia') and state_name ='Pennsylvania')
                or
                (co_name in ('Burlington', 'Camden', 'Gloucester', 'Mercer') and state_name = 'New Jersey')
            group by co_name, state_name
        """
        local_db.make_geotable_from_query(regional_counties, "regional_counties", "Polygon", 26918, schema="public")

        # Clip POIs to those inside DVRPC's region
        regional_pois = """
            select * from public.points_of_interest
            where st_intersects(geom, (select st_collect(geom) from public.regional_counties))
        """
        local_db.make_geotable_from_query(regional_counties, "regional_pois", "Point", 26918, schema="public")

    else:
        print("\n-> !!!Initial DB setup can only be executed from a DVRPC workstation!!!")


if __name__ == "__main__":

    pass

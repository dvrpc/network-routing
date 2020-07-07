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

See ``main.py``

"""

from postgis_helpers import PostgreSQL


def copy_production_data(remote_db: PostgreSQL, local_db: PostgreSQL):
    """
    Copy pedestrian network data from DVRPC's production SQL database
    to a SQL database on localhost.

    Note - this connection will only work within the firewall.
    """

    for table in ["pedestriannetwork_lines", "pedestriannetwork_points"]:

        query = f"SELECT * FROM transportation.{table};"
        gdf = remote_db.query_as_geo_df(query, geom_col="shape")
        gdf = gdf.rename(columns={"shape": "geometry"}).set_geometry("geometry")

        local_db.import_geodataframe(gdf, table)


if __name__ == "__main__":
    pass

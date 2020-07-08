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
from pathlib import Path
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

    # Custom query is needed for nj_centerline
    nj_centerline_query = """
        SELECT *, (ST_DUMP(shape)).geom
        FROM transportation.nj_centerline
    """

    nj_gdf = remote_db.query_as_geo_df(nj_centerline_query)

    # Remove 'nan's
    for idx, row in nj_gdf.iterrows():
        geom_txt = str(row["geom"])
        if "nan" in geom_txt:
            nj_gdf = nj_gdf.drop(idx)

    local_db.import_geodataframe(nj_gdf, "nj_centerlines")

    if "nj_centerline" not in local_db.all_spatial_tables_as_dict():
        print("ERROR! nj_centerline didn't make it! ")


def import_shapefiles(folder: Path, db: PostgreSQL):

    for shp_path in folder.rglob("*.shp"):

        pg_name = shp_path.name[:-4].replace(" ", "_").lower()

        db.import_geodata(pg_name, shp_path, if_exists="replace")


if __name__ == "__main__":

    pass

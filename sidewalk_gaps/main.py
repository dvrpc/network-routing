import postgis_helpers as pGIS
from postgis_helpers import PostgreSQL

from sidewalk_gaps.download_data import copy_production_data

local_db_credentials = pGIS.configurations()["localhost"]
dvrpc_db_credentials = pGIS.configurations()["dvrpc_gis"]

local_db = PostgreSQL("sidewalk_gaps", **local_db_credentials)
remote_db = PostgreSQL("gis", **dvrpc_db_credentials)


if __name__ == "__main__":
    # Copy the data to a local DB
    copy_production_data(remote_db, local_db)

    # Save the SQL database to file with pg_dump
    local_db.db_export_pgdump_file()
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import postgis_helpers as pGIS
import pg_data_etl as pg

from network_routing.accessibility.routable_network import RoutableNetwork

# Load environment variables
load_dotenv(find_dotenv())
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# Define downstream folder paths
GDRIVE_ROOT = os.getenv("GDRIVE_ROOT")
if GDRIVE_ROOT:
    GDRIVE_ROOT = Path(GDRIVE_ROOT)
    FOLDER_DATA_PRODUCTS = GDRIVE_ROOT / "My Drive/projects/RideScore/data products"
    GDRIVE_SW_GAPS_PROJECT_ROOT = GDRIVE_ROOT / "My Drive/projects/Sidewalk Gaps"
    GDRIVE_DATA = GDRIVE_ROOT / "Shared drives/network-routing-repo-data/data"

else:
    FOLDER_DATA_PRODUCTS, GDRIVE_SW_GAPS_PROJECT_ROOT, GDRIVE_DATA = None, None, None


def db_connection(database_name: str = DB_NAME, host: str = DB_HOST) -> pGIS.PostgreSQL:

    CREDENTIALS = pGIS.configurations()

    db = pGIS.PostgreSQL(database_name, verbosity="minimal", **CREDENTIALS[host])

    return db


def pg_db_connection(database_name: str = DB_NAME, host: str = DB_HOST) -> pg.Database:
    db = pg.Database.from_config(database_name, host)
    return db

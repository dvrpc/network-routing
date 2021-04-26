import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import postgis_helpers as pGIS

from network_routing.accessibility.routable_network import RoutableNetwork

# Load environment variables
load_dotenv(find_dotenv())
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# Define downstream folder paths
GDRIVE_ROOT = os.getenv("GDRIVE_ROOT")
if GDRIVE_ROOT:
    GDRIVE_ROOT = Path(GDRIVE_ROOT)
    FOLDER_DATA_PRODUCTS = GDRIVE_ROOT / "projects/RideScore/data products"
    GDRIVE_SW_GAPS_PROJECT_ROOT = GDRIVE_ROOT / "projects/Sidewalk Gaps"
else:
    FOLDER_DATA_PRODUCTS, GDRIVE_SW_GAPS_PROJECT_ROOT = None, None


def db_connection(database_name: str = DB_NAME, host: str = DB_HOST) -> pGIS.PostgreSQL:

    CREDENTIALS = pGIS.configurations()

    db = pGIS.PostgreSQL(database_name, verbosity="minimal", **CREDENTIALS[host])

    return db

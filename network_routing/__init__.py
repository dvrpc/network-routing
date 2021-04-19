import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import postgis_helpers as pGIS

from network_routing.accessibility.routable_network import RoutableNetwork

# Load environment variables
load_dotenv(find_dotenv())
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
GDRIVE_ROOT = Path(os.getenv("GDRIVE_ROOT"))

# Define downstream folder paths
FOLDER_DATA_PRODUCTS = GDRIVE_ROOT / "projects/RideScore/data products"
GDRIVE_SW_GAPS_PROJECT_ROOT = GDRIVE_ROOT / "projects/Sidewalk Gaps"


def db_connection(database_name: str = DB_NAME, host: str = DB_HOST) -> pGIS.PostgreSQL:

    CREDENTIALS = pGIS.configurations()

    db = pGIS.PostgreSQL(database_name, verbosity="minimal", **CREDENTIALS[host])

    return db

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import pg_data_etl as pg

import warnings
from shapely.errors import ShapelyDeprecationWarning

for warning in [FutureWarning, ShapelyDeprecationWarning]:
    warnings.simplefilter(action="ignore", category=warning)


from network_routing.accessibility.routable_network import RoutableNetwork

# Load environment variables
load_dotenv(find_dotenv())
DATABASE_URL = os.getenv("DATABASE_URL")

# Define downstream folder paths
GDRIVE_ROOT = os.getenv("GDRIVE_ROOT")
if GDRIVE_ROOT:
    GDRIVE_ROOT = Path(GDRIVE_ROOT)
    GDRIVE_DATA = GDRIVE_ROOT / "Shared drives/network-routing-repo-data/data"
    FOLDER_DATA_PRODUCTS = GDRIVE_DATA / "outputs"

else:
    FOLDER_DATA_PRODUCTS, GDRIVE_DATA = None, None


def pg_db_connection() -> pg.Database:
    db = pg.Database.from_uri(DATABASE_URL)
    return db

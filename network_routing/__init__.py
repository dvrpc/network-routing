import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

import postgis_helpers as pGIS

# import network_routing.accessibility as accessibility
from network_routing.accessibility.routable_network import RoutableNetwork


load_dotenv(find_dotenv())
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
GDRIVE_ROOT = os.getenv("GDRIVE_ROOT")


FOLDER_DATA_PRODUCTS = Path(GDRIVE_ROOT) / "projects/RideScore/data products"


def db_connection():

    CREDENTIALS = pGIS.configurations()

    db = pGIS.PostgreSQL(DB_NAME, verbosity="minimal", **CREDENTIALS[DB_HOST])

    return db

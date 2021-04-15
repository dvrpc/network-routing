import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

import postgis_helpers as pGIS

from .nodes import generate_nodes
from .routable_network import RoutableNetwork
from .generate_vector_tiles import make_vector_tiles
from .openstreetmap_extraction import import_osm_for_dvrpc_region

load_dotenv(find_dotenv())
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
GDRIVE_ROOT = os.getenv("GDRIVE_ROOT")

CREDENTIALS = pGIS.configurations()


def db_connection():
    return pGIS.PostgreSQL(DB_NAME, verbosity="minimal", **CREDENTIALS[DB_HOST])

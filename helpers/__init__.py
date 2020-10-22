import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

import postgis_helpers as pGIS

from .nodes import generate_nodes

load_dotenv(find_dotenv())
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
GDRIVE_ROOT = os.getenv("GDRIVE_ROOT")

CREDENTIALS = pGIS.configurations()


def db_connection():
    return pGIS.PostgreSQL(DB_NAME, **CREDENTIALS[DB_HOST])

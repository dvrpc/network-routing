"""
``sidewalk_gaps``
-----------------

The PROJECT_ROOT filepath is only accessible within the DVRPC firewall.

If you're connecting within WSL you'll need to first mount the U: drive:

    $ sudo mkdir /mnt/u
    $ sudo mount -t drvfs U: /mnt/u


GDRIVE_ROOT is accessible via MacOS and Windows.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv


# Define filepaths
load_dotenv(find_dotenv())
PROJECT_ROOT = os.getenv("PROJECT_ROOT")
GDRIVE_ROOT = os.getenv("GDRIVE_ROOT")

if PROJECT_ROOT:
    PROJECT_ROOT = Path(PROJECT_ROOT)
    FOLDER_SHP = PROJECT_ROOT / "shapefiles"
    FOLDER_SHP_INPUT = FOLDER_SHP / "inputs"
else:
    FOLDER_SHP, FOLDER_SHP_INPUT = None, None

if GDRIVE_ROOT:
    GDRIVE_ROOT = Path(GDRIVE_ROOT)
    GDRIVE_PROJECT_ROOT = GDRIVE_ROOT / "projects/Sidewalk Gaps"
    FOLDER_DB_BACKUPS = GDRIVE_PROJECT_ROOT / "database_dumps"
    FOLDER_DATA_PRODUCTS = GDRIVE_PROJECT_ROOT / "data products"
else:
    FOLDER_DB_BACKUPS, FOLDER_DATA_PRODUCTS = None, None

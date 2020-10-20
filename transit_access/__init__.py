from pathlib import Path

from postgis_helpers import PostgreSQL

from sidewalk_gaps import GDRIVE_ROOT, CREDENTIALS, PROJECT_DB_NAME

# Change Google Drive path to 'RideScore'
GDRIVE_ROOT = Path(str(GDRIVE_ROOT).replace("Sidewalk Gaps", "RideScore"))

db = PostgreSQL(PROJECT_DB_NAME, **CREDENTIALS["localhost"], verbosity="minimal")

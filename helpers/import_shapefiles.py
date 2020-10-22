from pathlib import Path
from postgis_helpers import PostgreSQL


def import_shapefiles(folder: Path, db: PostgreSQL):
    """ Import all shapefiles within a folder into SQL.
    """

    endings = [".shp", ".SHP"]

    for ending in endings:

        for shp_path in folder.rglob(f"*{ending}"):
            idx = len(ending) * -1
            pg_name = shp_path.name[:idx].replace(" ", "_").lower()
            db.import_geodata(pg_name, shp_path, if_exists="replace")

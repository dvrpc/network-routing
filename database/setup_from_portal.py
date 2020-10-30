import os
from pathlib import Path
import geopandas as gpd

from helpers import db_connection


data_to_download = [
    ("Transportation", ["PedestrianNetwork_lines",
                        "PedestrianNetwork_points",
                        "PassengerRailStations",
                        "TransitParkingFacilities",
                        ]),

    ("Boundaries", ["MunicipalBoundaries"]),
]

# Make a wget command for each table
commands = []

for schema, table_list in data_to_download:
    for tbl in table_list:
        wget_cmd = f'wget -O database/geojson/{tbl.lower()}.geojson "https://arcgis.dvrpc.org/portal/services/{schema}/{tbl}/MapServer/WFSServer?request=GetFeature&service=WFS&typename={tbl}&outputformat=GEOJSON&format_options=filename:{tbl.lower()}.geojson"'

        commands.append(wget_cmd)


if __name__ == "__main__":

    # Download GeoJSON data from DVRPC's ArcGIS REST portal
    for cmd in commands:
        os.system(cmd)

    # Import all of the geojson files into the SQL database
    db = db_connection()

    data_folder = Path(".")

    for geojson in data_folder.rglob("*.geojson"):
        gdf = gpd.read_file(geojson)

        sql_tablename = geojson.name.replace(".geojson", "")

        db.import_geodataframe(gdf, sql_tablename)

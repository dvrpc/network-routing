import os
from helpers import db_connection, GDRIVE_ROOT


tables_to_copy = {
    "network_routing_raw_data": [
        "regional_counties",
        "regional_pois",
        "transitparkingfacilities",
        "regional_transit_stops",
        "pedestriannetwork_lines",
        "passengerrailstations",
        "osm_edges",
        "municipalboundaries",
        "pedestriannetwork_points",

    ]
}


if __name__ == "__main__":

    # Copy data from source db
    for src_db in tables_to_copy:
        table_list = tables_to_copy[src_db]
        for table in table_list:
            cmd = f"db-import copy {src_db} localhost {table}"
            print(cmd)
            os.system(cmd)

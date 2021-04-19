from network_routing import db_connection, GDRIVE_SW_GAPS_PROJECT_ROOT


def setup_01_updated_ridescore_inputs():
    """
    Import the updated ridescore inputs showing access points to transit stations
    """

    db = db_connection()

    data_folder = GDRIVE_SW_GAPS_PROJECT_ROOT / "data-to-import"

    for filename_part in ["sw", "osm"]:
        filepath = data_folder / f"station_pois_for_{filename_part}.shp"
        db.import_geodata(f"ridescore_transit_poi_{filename_part}", filepath)


if __name__ == "__main__":
    setup_01_updated_ridescore_inputs()

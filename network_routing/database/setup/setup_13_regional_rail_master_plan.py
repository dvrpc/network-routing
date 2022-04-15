from network_routing import pg_db_connection


def setup_13_regional_rail_master_plan():
    """
    Make a cut of the access score data that just includes Regional Rail
    """

    db = pg_db_connection()

    db.gis_make_geotable_from_query(
        """
        select * from access_score_final_poi_set 
        where type = 'Commuter Rail'
    """,
        "regional_rail_master_plan_pois",
        "Point",
        26918,
    )


if __name__ == "__main__":
    setup_13_regional_rail_master_plan()

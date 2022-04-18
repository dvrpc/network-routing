from network_routing import pg_db_connection


def setup_14_eta_schools():
    """
    Make a cut of the access score data that just includes Regional Rail
    """

    db = pg_db_connection()

    db.gis_make_geotable_from_query(
        """
            select *, 'school' as placetype
            from eta_points
            where type in (
                'School - Private',
                'School - Public'
            )
    """,
        "eta_schools",
        "Point",
        26918,
    )


if __name__ == "__main__":
    setup_14_eta_schools()

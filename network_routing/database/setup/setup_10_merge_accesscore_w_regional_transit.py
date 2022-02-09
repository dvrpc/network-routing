from network_routing import pg_db_connection


def setup_10_merge_accessscore_w_regional_stops():
    """
    Merge open data regional transit stops with the
    'access score' points developed by DVRPC

    Regional transit stops include everything except
    SEPTA regional rail and 'highspeed', which is being
    pulled from DVRPC's accessscore layer
    """

    db = pg_db_connection()

    query = """
    with opendata as (
            select
                src as category,
                case
                    when stop_name is not null then stop_name
                    when station_na is not null then station_na
                    when stopname is not null then stopname
                    when station is not null then station
                    when description_bsl is not null then description_bsl
                    when route is not null then route
                    when station_id is not null then station_id
                end as poi_name,
                geom
            from
                regional_transit_stops
            where
                src not in ('SEPTA regional rail', 'SEPTA highspeed')
    ),
    accessscore as (
        select
            concat("operator", ' - ', "type") as category,
            concat(station, ' - ', line) as poi_name,
            geom
        from access_score_final_poi_set 
    )
    select * from opendata
    union
    select * from accessscore
    """

    db.gis_make_geotable_from_query(query, "regional_transit_with_accessscore", "POINT", 26918)


if __name__ == "__main__":
    setup_10_merge_accessscore_w_regional_stops()
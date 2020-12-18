from postgis_helpers import PostgreSQL
from sidewalk_gaps import FOLDER_DATA_PRODUCTS
from helpers import db_connection


def write_query_to_geojson(filename: str, query: str, db: PostgreSQL):
    """
    Write SQL query out to geojson file on disk.
    """

    # Put into Google Drive, if configured
    if FOLDER_DATA_PRODUCTS:
        output_filepath = FOLDER_DATA_PRODUCTS / f"{filename}.geojson"

    # Otherwise just drop it into the active directory
    else:
        output_filepath = f"{filename}.geojson"

    # Extract geodataframe from SQL
    df = db.query_as_geo_df(query)

    # Save to file
    df.to_file(output_filepath, driver="GeoJSON")


def export_webmap_data(db: PostgreSQL):
    """
    Export three geojson files:
        - centerlines
        - sw_nodes
        - transit_stops
    """

    # Centerlines with sidewalk amounts, as a ratio
    query_centerlines = """
        select hwy_tag, sw_ratio, state, st_transform(geom, 4326) as geom
        from data_viz.osm_sw_coverage
    """

    write_query_to_geojson("osm_sw_coverage", query_centerlines, db)

    # Transit accessibility results
    query_transit_results = """
        select
            uid,
            walk_time,
            st_transform(geom, 4326) as geom
        from
            data_viz.results_transit_access
    """
    write_query_to_geojson("sw_nodes", query_transit_results, db)

    # Transit stops
    query_transit_stops = """
        select
            uid,
            src,
            case
                when stop_name is not null then stop_name
                when station_name is not null then station_name
                when stopname is not null then stopname
                when station is not null then station
                when bsl is not null then bsl
                when on_street is not null then concat(on_street, ' @ ', at_street)
            end as stop_name,
            st_transform(geom, 4326) as geom
        from
            regional_transit_stops
        where
            st_within(
                geom,
                (select st_collect(geom) from regional_counties)
            )
    """
    write_query_to_geojson("transit_stops", query_transit_stops, db)

    # Islands of connectivity
    query_islands = """
        SELECT uid, rgba, st_transform(geom, 4326) as geom
        FROM data_viz.islands
    """
    write_query_to_geojson("islands", query_islands, db)


if __name__ == "__main__":

    db = db_connection()

    export_webmap_data(db)

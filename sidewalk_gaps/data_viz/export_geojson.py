from postgis_helpers import PostgreSQL
from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME, FOLDER_DATA_PRODUCTS


def write_query_to_geojson(
        filename: str,
        query: str,
        db: PostgreSQL):
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
    df.to_file(output_filepath,  driver="GeoJSON")


def export_webmap_data(db: PostgreSQL):
    """
        Export three geojson files:
            - centerlines
            - sw_nodes
            - transit_stops
    """

    # Centerlines with sidewalk amounts, as a ratio
    query_centerlines = """
        select
            sidewalk / st_length(geom) / 2 as sw,
            st_transform(geom, 4326) as geom
        from
            nj.centerlines

        union

        select
            sidewalk / st_length(geom) / 2 as sw,
            st_transform(geom, 4326) as geom
        from
            pa.centerlines
    """

    write_query_to_geojson("centerlines", query_centerlines, db)

    # Transit accessibility results
    query_transit_results = """
        select
            uid,
            walk_time,
            st_transform(geom, 4326) as geom
        from
            results_transit_access
    """
    write_query_to_geojson("sw_nodes", query_transit_results, db)

    # Transit stops
    query_transit_stops = """
        select
            uid,
            src,
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


if __name__ == "__main__":
    db = PostgreSQL(
        PROJECT_DB_NAME,
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )
    export_webmap_data(db)

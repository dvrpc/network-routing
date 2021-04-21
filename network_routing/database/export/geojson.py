from postgis_helpers import PostgreSQL
from network_routing import FOLDER_DATA_PRODUCTS, db_connection


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
    gdf = db.query_as_geo_df(query)

    # Ensure it's in the proper projection
    gdf = gdf.to_crs("EPSG:4326")

    # Save to file
    gdf.to_file(output_filepath, driver="GeoJSON")


def export_gap_webmap_data(db: PostgreSQL):
    """
    Export three geojson files:
        - centerlines
        - sw_nodes
        - transit_stops
    """

    # Centerlines with sidewalk amounts, as a ratio
    query_centerlines = """
        select hwy_tag, sidewalk / st_length(o.geom) / 2 as sw_ratio, st_transform(o.geom, 4326) as geom
        from public.osm_edges_all o
        inner join regional_counties c
        on st_within(o.geom, c.geom)
        where o.highway not like '%%motorway%%'
        and o.analyze_sw = 1
    """

    write_query_to_geojson("osm_sw_coverage", query_centerlines, db)

    # Transit accessibility results
    gdf_sample = db.query_as_geo_df(
        f"SELECT * FROM sw_defaults.regional_transit_stops_results LIMIT 1"
    )

    # Make a list of all columns that have 'n_1_' in their name
    cols_to_query = [col for col in gdf_sample.columns if "n_1_" in col]

    # Build a dynamic SQL query, getting the LEAST of the n_1_* columns
    query_base_results = "SELECT geom, LEAST(" + ", ".join(cols_to_query)
    query_base_results += f") as walk_time FROM sw_defaults.regional_transit_stops_results"

    write_query_to_geojson("sw_nodes", query_base_results, db)

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
        SELECT uid, size_miles, muni_names, muni_count, rgba, st_transform(geom, 4326) as geom
        FROM data_viz.islands
    """
    write_query_to_geojson("islands", query_islands, db)


def export_ridescore_webmap_data(db: PostgreSQL):

    tables_to_export = ["ridescore_isos", "sidewalkscore"]

    for tbl in tables_to_export:
        query = f"SELECT * FROM data_viz.{tbl}"
        write_query_to_geojson(tbl, query, db)


if __name__ == "__main__":

    db = db_connection()

    export_gap_webmap_data(db)
    export_ridescore_webmap_data(db)

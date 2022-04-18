from pathlib import Path
from pg_data_etl import Database
from network_routing import FOLDER_DATA_PRODUCTS


def write_query_to_geojson(filename: str, query: str, db: Database, folder: str):
    """
    Write SQL query out to geojson file on disk.
    """

    # Put into Google Drive, if configured
    if FOLDER_DATA_PRODUCTS:
        output_folder = FOLDER_DATA_PRODUCTS / folder

    # Otherwise just drop it into the active directory
    else:
        output_folder = Path(f"./{folder}")

    # Make sure the output folder exists
    output_folder.mkdir(exist_ok=True)

    # Define path to the file we're about to make
    output_filepath = output_folder / f"{filename}.geojson"

    # Extract geodataframe from SQL
    gdf = db.gdf(query)

    # Ensure it's in the proper projection
    gdf = gdf.to_crs("EPSG:4326")

    # Save to file
    gdf.to_file(output_filepath, driver="GeoJSON")


def export_rrmp_data(db: Database):
    write_query_to_geojson(
        "station_points", "select * from regional_rail_master_plan_pois", db, "rrmp"
    )
    write_query_to_geojson("isochrones", "select * from data_viz.rrmp_isochrones", db, "rrmp")


def export_gap_webmap_data(db: Database):
    """
    Export six geojson files:
        - centerlines
        - sw_nodes with transit results
        - transit_stops
        - islands of connectivity
        - eta schools
        - sidewalk nodes with transit results
    """

    # Centerlines with sidewalk amounts, as a ratio
    query_centerlines = """
        select hwy_tag, sidewalk / st_length(o.geom) / 2 as sw_ratio, st_transform(o.geom, 4326) as geom
        from public.osm_edges_drive o
        inner join regional_counties c
        on st_within(o.geom, c.geom)
        where o.highway not like '%%motorway%%'
        and o.analyze_sw = 1
    """

    write_query_to_geojson("osm_sw_coverage", query_centerlines, db, "gaps")

    # Transit accessibility results
    gdf_sample = db.gdf(f"SELECT * FROM sw_defaults.regional_transit_stops_results LIMIT 1")

    # Make a list of all columns that have 'n_1_' in their name
    cols_to_query = [col for col in gdf_sample.columns if "n_1_" in col]

    # Build a dynamic SQL query, getting the LEAST of the n_1_* columns
    query_base_results = "SELECT geom, LEAST(" + ", ".join(cols_to_query)
    query_base_results += f") as walk_time FROM sw_defaults.regional_transit_stops_results"

    write_query_to_geojson("sw_nodes", query_base_results, db, "gaps")

    # Transit stops
    query_transit_stops = """
        select * from regional_transit_with_accessscore
    """
    write_query_to_geojson("transit_stops", query_transit_stops, db, "gaps")

    # Islands of connectivity
    query_islands = """
        SELECT uid, size_miles, muni_names, muni_count, rgba, st_transform(geom, 4326) as geom
        FROM data_viz.islands
    """
    write_query_to_geojson("islands", query_islands, db, "gaps")

    # ETA Schools
    school_points = """
        select * from eta_schools
    """
    school_results = """
        select * from eta_schools.school_results
    """
    write_query_to_geojson("school_points", school_points, db, "gaps")
    write_query_to_geojson("school_results", school_results, db, "gaps")


def export_accessscore_webmap_data(db: Database):
    """
    Export data for the ridescore analysis
    - isochrones
    - single-point "sidewalkscore" for each station
    - multi-point access inputs (multiple points per station)
    """

    tables_to_export = [
        "data_viz.accessscore_results",
        "data_viz.accessscore_points",
        "public.access_score_final_poi_set",
    ]

    for tbl in tables_to_export:
        query = f"SELECT * FROM {tbl}"

        schema, tablename = tbl.split(".")

        write_query_to_geojson(tablename, query, db, "gaps")


def export_county_specific_data(db: Database):
    """
    Export data for the MCPC-specific visualization:

    - ETA points with county name as text
    - Isochrones for all montco ETA points TODO
    - 'missing sidewalks' with priority results? TODO
    """

    mcpc_combined_pois_full = """
        select *
        from data_viz.ab_ratio_mcpc_combined_pois
        where category != 'NJT rail'
    """
    mcpc_combined_pois_centroids = """
        with centroids as (
                select
                    poi_name, category, poi_uid, ab_ratio, st_centroid(st_collect(geom)) as geom
                from
                    data_viz.ab_ratio_mcpc_combined_pois
                where category != 'NJT rail'
                group by
                    poi_name, category, poi_uid, ab_ratio
        )

        select
            st_collect(geom) as geom, 
            poi_name, 
            category, 
            min(poi_uid) as poi_uid, 
            ab_ratio
        from
            centroids
        group by
            poi_name, category, ab_ratio, geom
    """
    eta_isos = """
        select * from data_viz.isochrones_mcpc_combined_pois
    """
    montco_missing_sidewalks = """
        select * from improvements.montgomery_split
    """

    queries = {
        "pois_full": mcpc_combined_pois_full,
        "pois_centroids": mcpc_combined_pois_centroids,
        "mcpc_isos": eta_isos,
        "montco_missing_sidewalks": montco_missing_sidewalks,
    }

    for filename, query in queries.items():
        print(filename, query)

        write_query_to_geojson(filename, query, db, "mcpc")


def export_septa_data(db: Database):
    """
    Export data for SEPTA
    """

    pois = """
        select src_table, stop_id, ab_ratio, geom 
        from data_viz.ab_ratio_pois_for_septa_tod_analysis
    """
    isos = """
        select eta_uid as stop_id, src_network, geom 
        from data_viz.isochrones_pois_for_septa_tod_analysis
    """

    queries = {
        "septa_stops": pois,
        "walksheds": isos,
    }

    for filename, query in queries.items():
        print(filename, query)

        write_query_to_geojson(filename, query, db, "septa")


def export_PART_data(db: Database):
    """
    Export data for PART
    """

    pois = """
        select * from data_viz.part_pois_with_scores
    """
    isos = """
        select * from data_viz.part_isos
    """
    raw_sw = """
        select * from part_sw.pois_results
    """
    raw_osm = """
        select * from part_osm.pois_results
    """

    queries = {"pois": pois, "walksheds": isos, "raw_sw": raw_sw, "raw_osm": raw_osm}

    for filename, query in queries.items():
        print(filename, query)

        write_query_to_geojson(filename, query, db, "PART")


def export_dock_data(db: Database):
    """
    Export data for NJ docks
    """
    isos = """
        select * from data_viz.dock_isos
    """
    raw_sw = """
        select * from docks_sw.docks_sidewalk_results
    """
    raw_osm = """
        select * from docks_osm.docks_open_street_results
    """

    queries = {"walksheds": isos, "raw_sw": raw_sw, "raw_osm": raw_osm}

    for filename, query in queries.items():
        print(filename, query)

        write_query_to_geojson(filename, query, db, "Dock")


def export_regional_gap_data(db: Database):
    """
    Export data showing all gaps across the region
    """
    filename = "regional_sidewalk_gaps"
    query = """
        with all_gaps as (
                  select geom from improvements.gloucester_erased
            union select geom from improvements.camden_erased
            union select geom from improvements.burlington_erased
            union select geom from improvements.mercer_erased
            union select geom from improvements.montgomery_erased
            union select geom from improvements.bucks_erased
            union select geom from improvements.chester_erased
            union select geom from improvements.delaware_erased
            union select geom from improvements.philadelphia_erased
        )
        select
            row_number() over () as uid,
            geom
        from all_gaps
    """

    write_query_to_geojson(filename, query, db, "regional_gaps")


if __name__ == "__main__":
    pass

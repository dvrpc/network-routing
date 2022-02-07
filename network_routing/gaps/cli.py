"""
`gaps`
------

`gaps` is the command-line-interface for the `network_routing.gaps` module.

Examples:
    Classify the OSM centerlines by sidewalk coverage

    ```shell
    > gaps classify-osm-sw-coverage
    ```

    You can also see a list of all available configurations by running `gaps --help`

    ```shell
    > gaps --help

    Usage: gaps [OPTIONS] COMMAND [ARGS]...

    The command 'gaps' is used for segment-specific gap analyses

    Options:
    --help  Show this message and exit.

    Commands:
    classify-osm-sw-coverage  Classify OSM w/ length of parallel sidewalks
    identify-islands          Join intersecting sidewalks to create 'islands'
    isochrones                Turn access results into isochrone polygons
    scrub-osm-tags            Clean 'highway' tags in the OSM data
    sidewalkscore             Calculate the SidewalkScore for each rail stop
    ```

"""

import click

from network_routing import pg_db_connection

from network_routing.gaps.segments.centerline_sidewalk_coverage import (
    classify_centerlines,
)
from network_routing.gaps.segments.generate_islands import generate_islands

from network_routing.gaps.data_viz.handle_osm_tags import (
    scrub_osm_tags as _scrub_osm_tags,
)
from network_routing.gaps.data_viz.ridescore_isochrones import (
    generate_isochrones,
    calculate_sidewalkscore,
)
from network_routing.gaps.data_viz.access_score_results import (
    main as access_score_results_main,
)
from network_routing.gaps.data_viz.eta_isochrones import IsochroneGenerator


@click.group()
def main():
    "The command 'gaps' is used for segment-specific gap analyses"
    pass


@click.command()
def classify_osm_sw_coverage():
    """Classify OSM w/ length of parallel sidewalks"""

    db = pg_db_connection()

    classify_centerlines(db, "osm_edges_drive")


@click.command()
def identify_islands():
    """Join intersecting sidewalks to create 'islands'"""

    db = pg_db_connection()

    generate_islands(db)


@click.command()
def isochrones_accessscore():
    """
    Make 'Access Score' isos & POIs with stats
    """

    db = pg_db_connection()

    generate_isochrones(db)

    query = """
        select
            st_centroid(st_collect(geom)) as geom,
            type, line, station, operator, dvrpc_id as poi_uid
        from access_score_final_poi_set
        group by type, line, station, operator, dvrpc_id 
        order by dvrpc_id
    """

    calculate_sidewalkscore(db, query)


@click.command()
def accessscore_line_results():
    """
    Export line results from Access Score analysis
    """
    access_score_results_main()


@click.command()
def isochrones_mcpc():
    """
    Make isos & POIs with stats for MCPC

    """
    db = pg_db_connection()

    args = {
        "db": db,
        "poi_table": f"mcpc_combined_pois",
        "poi_col": "poi_uid",
        "network_a_edges": "pedestriannetwork_lines",
        "network_a_nodes": "nodes_for_sidewalks",
        "network_a_node_id_col": "sw_node_id",
        "network_b_edges": "osm_edges_all_no_motorway",
        "network_b_nodes": "nodes_for_osm_all",
        "network_b_node_id_col": "node_id",
        "data_dir": "./data",
    }

    i = IsochroneGenerator(**args)
    i.save_isos_to_db()
    i.save_pois_with_iso_stats_to_db()


@click.command()
def isochrones_septa():
    """
    Make SEPTA isos & POIs with stats

    """
    db = pg_db_connection()

    args = {
        "db": db,
        "poi_table": f"pois_for_septa_tod_analysis",
        "poi_col": "stop_id",
        "network_a_edges": "pedestriannetwork_lines",
        "network_a_nodes": "nodes_for_sidewalks",
        "network_a_node_id_col": "sw_node_id",
        "network_b_edges": "osm_edges_all_no_motorway",
        "network_b_nodes": "nodes_for_osm_all",
        "network_b_node_id_col": "node_id",
        "data_dir": "./data",
        "distance_threshold_miles": 0.25,
    }

    i = IsochroneGenerator(**args)
    i.save_isos_to_db()
    i.save_pois_with_iso_stats_to_db()


@click.command()
def isochrones_part():
    """
    Make PART isos & POIs with stats
    """

    db = pg_db_connection()

    # Generate isochrones
    iso_args = {
        "sidewalk_result_table": "part_sw.pois_results",
        "osm_result_table": "part_osm.pois_results",
        "output_tablename": "data_viz.part_isos",
    }

    generate_isochrones(db, **iso_args)

    # Generate a point layer that summarizes the isochrone results
    query = """
        select 
        replace(
            replace(
                replace(lower(name), ' ', ''),
                '-',
                ''
            ),
            '/',
            ''
        ) as poi_uid, *
        from part
    """

    final_point_args = {
        "poi_query": query,
        "uid_col": "poi_uid",
        "osm_schema": "part_osm",
        "sw_schema": "part_sw",
        "iso_table": "data_viz.part_isos",
        "output_tablename": "data_viz.part_pois_with_scores",
    }

    calculate_sidewalkscore(db, **final_point_args)


@click.command()
def scrub_osm_tags():
    """Clean 'highway' tags in the OSM data"""

    db = pg_db_connection()

    _scrub_osm_tags(db)


_all_commands = [
    classify_osm_sw_coverage,
    identify_islands,
    scrub_osm_tags,
    isochrones_accessscore,
    isochrones_mcpc,
    accessscore_line_results,
    isochrones_septa,
    isochrones_part,
]

for cmd in _all_commands:
    main.add_command(cmd)

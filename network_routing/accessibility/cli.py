"""
`access`
--------


`access` is the command-line-interface for the `network_routing.accessibility` module.

A number of configurations are pre-defined, all of which can be found within [`network_routing/accessibility/cli.py`](https://github.com/dvrpc/network-routing/blob/master/network_routing/accessibility/cli.py).


Examples:
    Run the default analysis:

    ```shell
    > access sw-default
    ```

    Run the Ridescore analysis:

    ```shell
    > access sw-ridescore
    > access osm-ridescore
    ```


    You can also see a list of all available configurations by running `access --help`

    ```shell
    > access --help

    Usage: access [OPTIONS] COMMAND [ARGS]...

    The command 'access' is used to run an accessibility analysis against
    point-of-interest + network edge datasets

    Options:
    --help  Show this message and exit.

    Commands:
    osm-ridescore  Analyze OSM network distance around each rail stop
    sw-default     Run the RoutableNetwork with default settings
    sw-ridescore   Analyze sidewalk network distance around each rail stop
    ```

"""
import click
from datetime import datetime

from network_routing import pg_db_connection

from .routable_network import RoutableNetwork, DoubleNetwork


def _execute_analysis_into_one_output(arguments: dict) -> RoutableNetwork:
    """
    Print the analysis parameters before running
    """

    # Print parameters and start time
    print(f"Executing an accessibility analysis with the following arguments:")
    for k, v in arguments.items():
        print(f"\t -> {k} = {v}")

    print("Beginning at:", datetime.now())

    # Run analysis
    db = pg_db_connection()
    net = RoutableNetwork(db, **arguments)
    net.compute_every_poi_into_one_postgres_table()

    return net


@click.group()
def main():
    """The command 'access' is used to run an accessibility analysis
    against point-of-interest + network edge datasets"""
    pass


@click.command()
def sw_default():
    """Run the RoutableNetwork with default settings """

    arguments = {
        "edge_table_name": "pedestriannetwork_lines",
        "node_table_name": "nodes_for_sidewalks",
        "node_id_column": "sw_node_id",
        "poi_table_name": "regional_transit_stops",
        "poi_id_column": "src",
        "output_table_name": "regional_transit_stops",
        "output_schema": "sw_defaults",
        "max_minutes": 180,
        "poi_match_threshold": 152,  # aka 500'
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
def osm_access_score():
    """Rail stops w/ OSM network (including highways)"""

    arguments = {
        "poi_table_name": "access_score_final_poi_set",
        "poi_id_column": "dvrpc_id",
        "output_table_name": "osm",
        "output_schema": "access_score_osm",
        "num_pois": 1,
        "max_minutes": 50,  # 48 minutes = 2 miles @ 2.5 mph
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "osm_edges_all",
        "node_table_name": "nodes_for_osm_all",
        "node_id_column": "node_id",
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
def lowstress_access_score():
    """Rail stops w/ low-stress bicycle network"""

    arguments = {
        "poi_table_name": "access_score_final_poi_set",
        "poi_id_column": "dvrpc_id",
        "output_table_name": "lts",
        "output_schema": "access_score_lts",
        "num_pois": 1,
        "max_minutes": 50,  # 48 minutes = 2 miles
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "lowstress_islands",
        "node_table_name": "nodes_for_lowstress_islands",
        "node_id_column": "node_id",
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
def sw_access_score():
    """Rail stops w/ sidewalk network"""

    arguments = {
        "poi_table_name": "access_score_final_poi_set",
        "poi_id_column": "dvrpc_id",
        "output_table_name": "sw",
        "output_schema": "access_score_sw",
        "num_pois": 1,
        "max_minutes": 50,  # 48 minutes = 2 miles
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "pedestriannetwork_lines",
        "node_table_name": "nodes_for_sidewalks",
        "node_id_column": "sw_node_id",
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
def sw_eta():
    """ETA points by category w/ sidewalk network"""

    arguments = {
        "poi_table_name": "eta_points",
        "poi_id_column": "type",
        "output_table_name": "sw_eta",
        "output_schema": "sw_eta",
        "num_pois": 3,
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "pedestriannetwork_lines",
        "node_table_name": "nodes_for_sidewalks",
        "node_id_column": "sw_node_id",
        "max_minutes": 180,
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
def osm_eta():
    """ETA points by catgory w/ OSM network """

    arguments = {
        "poi_table_name": "eta_points",
        "poi_id_column": "type",
        "output_table_name": "osm_eta",
        "output_schema": "osm_eta",
        "num_pois": 3,
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "osm_edges_all_no_motorway",
        "node_table_name": "nodes_for_osm_all",
        "node_id_column": "node_id",
        "max_minutes": 45,
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
@click.argument("county")
def eta_individual(county):
    """Analyze each individual ETA point within the 'county`, using both the OSM and sidewalk network.

    Results are written to CSV files on disk.
    """

    county = county.lower()

    db = pg_db_connection()

    dn = DoubleNetwork(
        db,
        shared_args={
            "poi_table_name": "mcpc_combined_pois",
            "poi_id_column": "poi_uid",
            "max_minutes": 45,
            "num_pois": 1,
            "poi_match_threshold": 152,  # aka 500'
        },
        network_a_args={
            "edge_table_name": "osm_edges_all_no_motorway",
            "node_table_name": "nodes_for_osm_all",
            "node_id_column": "node_id",
        },
        network_b_args={
            "edge_table_name": "pedestriannetwork_lines",
            "node_table_name": "nodes_for_sidewalks",
            "node_id_column": "sw_node_id",
        },
    )

    dn.compute()


@click.command()
def srts_before_after():
    """Model the impact of a set of new sidewalk improvements"""

    db = pg_db_connection()

    tablename = "mcpc_srts_projects_with_existing_network"
    network_tag_col = "groupid"
    base_network_tag = "EXISTING NETWORK"

    all_network_tags_to_analyze = db.query_as_list_of_singletons(
        f"""select distinct {network_tag_col}
            from {tablename}
            where {network_tag_col} != '{base_network_tag}'"""
    )

    shared_arguments = {
        "poi_table_name": "mcpc_school_pois",
        "poi_id_column": "category",
        "num_pois": 3,
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": tablename,
        "node_table_name": f"nodes_for_{tablename}",
        "node_id_column": "node_id",
        "max_minutes": 50,  # 48 minutes = 2 miles
    }

    # Run a network analysis for each tag in the SRTS table
    for tag in all_network_tags_to_analyze:
        print("#" * 80)
        print(f"RUNNING: {tag}")
        edge_network_filter = f"{network_tag_col} in ('{base_network_tag}', '{tag}')"

        tag_sql = tag.lower().replace(" ", "_")

        custom_arguments = {
            "output_table_name": tag_sql,
            "output_schema": f"srts_{tag_sql}",
            "edge_table_where_query": edge_network_filter,
        }

        _ = _execute_analysis_into_one_output({**shared_arguments, **custom_arguments})

    # Run a final analysis using just the base network

    print("#" * 80)
    print(f"RUNNING: BASE NETWORK")

    custom_arguments = {
        "output_table_name": "base_network",
        "output_schema": f"srts_base_network",
        "edge_table_where_query": f"{network_tag_col} = '{base_network_tag}' ",
    }

    _ = _execute_analysis_into_one_output({**shared_arguments, **custom_arguments})

    # Make an example summary
    example_id = "eisenhower"
    query = f""" 
        select 
            n.node_id, 
            b.n_1_publicschool as base_net_dist,
            s.n_1_publicschool as new_net_dist,
            b.n_1_publicschool - s.n_1_publicschool as diff,
            n.geom
        from
            nodes_for_{tablename} n
        left join
            srts_base_network.base_network_results b
        on
            b.node_id = n.node_id::text
        left join
            srts_{example_id}.{example_id}_results s
        on
            s.node_id = n.node_id::text
    """
    db.gis_make_geotable_from_query(query, "data_viz.example_mcpc_srts", "POINT", 26918)


_all_commands = [
    sw_default,
    osm_access_score,
    lowstress_access_score,
    sw_access_score,
    sw_eta,
    osm_eta,
    eta_individual,
    srts_before_after,
]

for cmd in _all_commands:
    main.add_command(cmd)


if __name__ == "__main__":
    pass

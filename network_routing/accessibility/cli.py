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
def osm_ridescore():
    """Analyze OSM network distance around each rail stop """

    arguments = {
        "poi_table_name": "ridescore_pois",
        "poi_id_column": "dvrpc_id",
        "output_table_name": "osm",
        "output_schema": "rs_osm",
        "num_pois": 1,
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "osm_edges_all",
        "node_table_name": "nodes_for_osm_all",
        "node_id_column": "node_id",
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
def sw_ridescore():
    """Analyze sidewalk network distance around each rail stop """

    arguments = {
        "poi_table_name": "ridescore_pois",
        "poi_id_column": "dvrpc_id",
        "output_table_name": "sw",
        "output_schema": "rs_sw",
        "num_pois": 1,
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "pedestriannetwork_lines",
        "node_table_name": "nodes_for_sidewalks",
        "node_id_column": "sw_node_id",
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
def sw_eta():
    """Analyze sidewalk network distance for each 'type' of ETA point """

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
    """Analyze OSM network distance for each 'type' of ETA point """

    arguments = {
        "poi_table_name": "eta_points",
        "poi_id_column": "type",
        "output_table_name": "osm_eta",
        "output_schema": "osm_eta",
        "num_pois": 3,
        "poi_match_threshold": 152,  # aka 500'
        "edge_table_name": "osm_edges_all",
        "node_table_name": "nodes_for_osm_all",
        "node_id_column": "node_id",
        "max_minutes": 45,
    }

    _ = _execute_analysis_into_one_output(arguments)


@click.command()
@click.argument("county")
def eta_individual(county):
    """
    Analyze network distance for each individual ETA point within the 'county`,
    using both the OSM and sidewalk network.

    Results are written to CSV files on disk.
    """

    county = county.lower()

    db = pg_db_connection()

    dn = DoubleNetwork(
        db,
        shared_args={
            "poi_table_name": f"eta_{county}",
            "poi_id_column": "eta_uid",
            "max_minutes": 45,
            "num_pois": 1,
            "poi_match_threshold": 152,  # aka 500'
        },
        network_a_args={
            "edge_table_name": "osm_edges_all",
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


_all_commands = [
    sw_default,
    osm_ridescore,
    sw_ridescore,
    sw_eta,
    osm_eta,
    eta_individual,
]

for cmd in _all_commands:
    main.add_command(cmd)


if __name__ == "__main__":
    pass

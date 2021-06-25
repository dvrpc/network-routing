"""
logic_prep.py
-------------

This module contains functions that prepare GIS data for network analysis

"""
from __future__ import annotations

import geopandas as gpd
import pandana as pdna

from pg_data_etl import Database


def assign_node_ids_to_network(
    db: Database, edge_table_name: str, node_table_name: str, node_id_column: str
) -> None:
    """
    - Starting with an edge table and companion node table, this function
    adds `start_id` and `end_id` columns to the edge table and populates each
    record with the ID of the node at the start and end of the segment

    Arguments:
        db (Database): analysis postgresql database
        edge_table_name (str): name of the edge table
        node_table_name (str): name of the companion node table
        node_id_column (str): name of the unique ID column in the node table

    Returns:
        None: but updates the `edge_table_name` in-place with new columns and values within
    """

    print(f"Assigning Node ID values to {edge_table_name}")

    # Add columns for the start and end node_id values
    for column_name in ["start_id", "end_id"]:
        query = f"""
            ALTER TABLE {edge_table_name}
            ADD COLUMN {column_name} INT;
        """
        db.execute(query)

    # Execute the query for the START of each segment
    start_id_query = f"""
        UPDATE {edge_table_name} ln
        SET start_id = (
            SELECT pt.{node_id_column}
            FROM {node_table_name} pt
            WHERE 
                ST_DWITHIN(
                    pt.geom,
                    st_startpoint(ln.geom),
                    5
                )
            ORDER BY
                ST_DISTANCE(
                    pt.geom,
                    st_startpoint(ln.geom)
                )
                ASC LIMIT 1
        )
    """
    db.execute(start_id_query)

    # Execute the query for the END of each segment
    end_id_query = start_id_query.replace("start", "end")
    db.execute(end_id_query)


def add_travel_time_weights_to_network(
    db: Database, edge_table_name: str, walking_mph: float = 2.5
):
    """
    Add impedence columns to the edges:

    1) Calculate the legnth in meters (epsg:26918)
    2) Convert meters into minutes:
        - divide by 1609.34
        - divide by defined walking speed in MPH
        - multiply by 60 to get minutes

    Arguments:
        db (Database): analysis postgresql database
        edge_table_name (str): name of the edge table
        walking_mph (float): speed of pedestrians in miles-per-hour

    Returns:
        None: but updates the `edge_table_name` in-place with new columns and values within


    """

    print(f"Adding travel time weights to {edge_table_name}")

    # Add a meter length and minutes column
    for column_name in ["len_meters", "minutes"]:
        query = f"""
            ALTER TABLE {edge_table_name}
            ADD COLUMN {column_name} FLOAT;
        """
        db.execute(query)

    # Capture length in meters into its own column
    update_meters = f"""
        UPDATE {edge_table_name}
        SET len_meters = ST_LENGTH(geom);
    """
    db.execute(update_meters)

    # Calculate walking travel time in minutes
    update_minutes = f"""
        UPDATE {edge_table_name}
        SET minutes = len_meters / 1609.34 / {walking_mph} * 60;
    """
    db.execute(update_minutes)


def construct_network(
    db: Database,
    edge_table_name: str,
    node_table_name: str,
    node_id_column: str,
    max_minutes: float,
) -> tuple[pdna.Network, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Turn edge and node data from PostGIS into a `pandana.Network`

    Arguments:
        db (Database): analysis postgresql database
        edge_table_name (str): name of the edge table
        node_table_name (str): name of the companion node table
        node_id_column (str): name of the unique ID column in the node table
        max_minutes (float): the maximum distance in minutes that you intend to analyze

    Returns:
        pdna.Network: built using edges and nodes from arguments, and precomputed to `max_minutes`
        gpd.GeoDataFrame: edge geodataframe
        gpd.GeoDataFrame: node geodataframe
    """

    # Get all edges
    query = f"""
        SELECT start_id, end_id, minutes, geom
        FROM {edge_table_name}
        WHERE start_id IN (
                select distinct {node_id_column}
                FROM {node_table_name}
            )
            AND
            end_id IN (
                select distinct {node_id_column}
                FROM {node_table_name}
            )
    """
    edge_gdf = db.gdf(query)

    # Get all nodes
    node_query = f"""
        SELECT {node_id_column} AS node_id,
            ST_X(st_transform(geom, 4326)) as x,
            ST_Y(st_transform(geom, 4326)) as y,
            geom
        FROM {node_table_name}
    """
    node_gdf = db.gdf(node_query)

    # Force the ID columns in the edge gdf to integer
    for col in ["start_id", "end_id"]:
        edge_gdf[col] = edge_gdf[col].astype(int)

    # Set the index of the NODE gdf to the uid column
    node_gdf.set_index("node_id", inplace=True)

    # Build the pandana network
    print("Making network")
    network = pdna.Network(
        node_gdf["x"],
        node_gdf["y"],
        edge_gdf["start_id"],
        edge_gdf["end_id"],
        edge_gdf[["minutes"]],
        twoway=True,
    )

    print("Precomputing the network")
    network.precompute(max_minutes)

    return network, edge_gdf, node_gdf

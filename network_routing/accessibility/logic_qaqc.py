from __future__ import annotations

from sqlalchemy import create_engine
import pandas as pd
import geopandas as gpd
import pandana as pdna
from shapely.geometry import LineString
from geoalchemy2 import Geometry, WKTElement

from pg_data_etl import Database


def qaqc_poi_assignment(
    db: Database,
    network: pdna.Network,
    poi_uid_cleaned: str,
    poi_gdf: gpd.GeoDataFrame,
    node_gdf: gpd.GeoDataFrame,
    epsg: int = 26918,
):
    """
    For a given poi geodataframe:
        1) Get the ID of the nearest node for each POI
        2) Add a 'flow' geometry from the POI to the assigned node
        3) Delete all other geometry columns in the table and write to SQL

    Arguments:
        db (Database): analysis postgresql database
        network (pdna.Network): network model to use
        poi_uid_cleaned (str): cleaned version of unique ID value for one or a set of POIs
        poi_gdf (gpd.GeoDataFrame): geodataframe with POI(s) being analyzed
        node_gdf (gpd.GeoDataFrame): geodataframe with network nodes
        epsg (int): spatial data projection, defaults to `26918`

    Returns:
        None: but makes a new table named `qaqc.qa_{poi_uid}`
    """

    # Save the network assignment for QAQC
    poi_gdf["node_id"] = network.get_node_ids(poi_gdf["x"], poi_gdf["y"], mapping_distance=1)
    poi_node_pairs = pd.merge(
        poi_gdf,
        node_gdf,
        left_on="node_id",
        right_on="node_id",
        how="left",
        sort=False,
        suffixes=["_from", "_to"],
    )

    poi_node_pairs["flow"] = [
        LineString([row["geom_from"], row["geom_to"]]) for idx, row in poi_node_pairs.iterrows()
    ]
    poi_node_pairs = poi_node_pairs.set_geometry("flow")

    poi_node_pairs["geom"] = poi_node_pairs["flow"].apply(lambda x: WKTElement(x.wkt, srid=epsg))

    for col in ["flow", "geom_from", "geom_to"]:
        poi_node_pairs.drop(col, inplace=True, axis=1)

    sql_tablename = f"qa_{poi_uid_cleaned}"

    engine = create_engine(db.uri)
    poi_node_pairs.to_sql(
        sql_tablename,
        engine,
        schema="qaqc",
        if_exists="replace",
        dtype={"geom": Geometry("LineString", srid=epsg)},
    )
    engine.dispose()

    return None


def clean_up_qaqc_tables(db: Database, output_schema: str, poi_id_column: str):

    # Make sure the output_schema exists
    schema_query = f"""
        CREATE SCHEMA IF NOT EXISTS {output_schema};
    """
    db.execute(schema_query)

    # Get a list of all tables in the 'qaqc' schema
    qa_tables = db.tables(schema="qaqc")

    # Merge all QAQC tables together if there's more than 1
    if len(qa_tables) == 1:
        query = f"SELECT {poi_id_column}, geom FROM {qa_tables[0]}"
    else:

        qa_subqueries = [f"SELECT {poi_id_column}, geom FROM {x}" for x in qa_tables]

        query = """
            UNION
        """.join(
            qa_subqueries
        )

    # Write combined QAQC tables to output schema as one unified table
    output_tablename = f"{output_schema}.qaqc_node_match"
    db.gis_make_geotable_from_query(
        query,
        output_tablename,
        "LINESTRING",
        26918,
    )

    # Delete the original tables under the 'qaqc' schema
    for qa_table in qa_tables:
        db.execute(
            f"""
            DROP TABLE {qa_table};
        """
        )

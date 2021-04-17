import click
import os
from random import randint

from network_routing import db_connection

# from .hexagon_summary import hexagon_summary, classify_hex_results
from .handle_osm_tags import scrub_osm_tags as _scrub_osm_tags
from .combine_network_analysis_results import (
    combine_transit_results as _combine_transit_results,
)
from .ridescore_isochrones import generate_isochrones, calculate_sidewalkscore


@click.command()
def isochrones():
    """Turn access results into isochrone polygons"""

    db = db_connection()

    generate_isochrones(db)


@click.command()
def sidewalkscore():
    """Calculate the SidewalkScore for each rail stop"""

    db = db_connection()

    calculate_sidewalkscore(db)


@click.command()
def combine_centerlines():
    """ Merge PA and NJ OSM segments together """
    db = db_connection()

    query = """
        select
            osmid, name, highway, sidewalk, st_length(geom) as len_meters,
            sidewalk / st_length(geom) / 2 as sw_ratio,
            'NJ' as state,
            geom
        from
            nj.osm_edges

        union

        select
            osmid, name, highway, sidewalk, st_length(geom) as len_meters,
            sidewalk / st_length(geom) / 2 as sw_ratio,
            'PA' as state,
            geom
        from
            pa.osm_edges
    """
    kwargs = {"geom_type": "LineString", "epsg": 26918, "schema": "data_viz"}
    db.make_geotable_from_query(query, "osm_sw_coverage", **kwargs)


# @click.command()
# def combine_islands():
#     """ Merge the NJ and PA island analyses """

#     db = db_connection()

#     query = """
#         SELECT geom FROM nj.islands
#         UNION
#         SELECT geom FROM pa.islands
#     """
#     kwargs = {"geom_type": "MultiLineString", "epsg": 26918, "schema": "data_viz"}
#     db.make_geotable_from_query(query, "islands", **kwargs)

#     # Add a column for size
#     db.table_add_or_nullify_column("islands", "size_miles", "FLOAT", schema="data_viz")

#     query = "UPDATE data_viz.islands SET size_miles = ST_LENGTH(geom) * 0.000621371;"
#     db.execute(query)

#     # For each island, make a rgba() string with random values

#     # Add a column for rgba
#     db.table_add_or_nullify_column("islands", "rgba", "TEXT", schema="data_viz")

#     # Get a count of the rows
#     query = "SELECT uid FROM data_viz.islands"
#     uids = db.query_as_df(query)
#     for idx, row in uids.iterrows():

#         r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
#         rgba = f"rgba({r}, {g}, {b}, 1)"

#         query = f"""
#             UPDATE data_viz.islands
#             SET rgba = '{rgba}'
#             WHERE uid = {row.uid}
#         """
#         db.execute(query)


@click.command()
def combine_transit_results():
    """ Merge the NJ and PA accessibility analysis """

    db = db_connection()

    _combine_transit_results(db)


@click.command()
def scrub_osm_tags():
    """ Clean 'highway' tags in the OSM data """

    db = db_connection()

    _scrub_osm_tags(db)


# @click.command()
# def summarize_into_hexagons():
#     """ Classify centerlines w/ length of parallel sidewalks """

#     db = db_connection()

#     hexagon_summary(db)


# @click.command()
# def classify_hexagons():
#     """ Prepare analysis result for bivariate choropleth map """

#     db = db_connection()

#     classify_hex_results(db)

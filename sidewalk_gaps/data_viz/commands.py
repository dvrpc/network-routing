import click
import os

from helpers import db_connection
from helpers import make_vector_tiles as _make_vector_tiles
from sidewalk_gaps import FOLDER_DATA_PRODUCTS
# from .hexagon_summary import hexagon_summary, classify_hex_results
from .handle_osm_tags import scrub_osm_tags as _scrub_osm_tags
from .combine_network_analysis_results import combine_transit_results as _combine_transit_results
from .export_geojson import export_webmap_data


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
    kwargs = {
        'geom_type': "LineString",
        'epsg': 26918,
        'schema': "data_viz"
    }
    db.make_geotable_from_query(query, "osm_sw_coverage", **kwargs)


@click.command()
def combine_transit_results():

    db = db_connection()

    _combine_transit_results(db)


@click.command()
def scrub_osm_tags():
    """ Clean 'highway' tags in the OSM data """
    _scrub_osm_tags()


@click.command()
def export_geojson_for_webmap():
    """Save .geojson files to be tiled for webmaps"""
    db = db_connection()

    export_webmap_data(db)


@click.command()
def make_vector_tiles():

    _make_vector_tiles(FOLDER_DATA_PRODUCTS, "sidewalk_gaps_analysis")


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

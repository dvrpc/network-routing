import os
import platform
import socket
from pathlib import Path
import geopandas as gpd
from geopandas import GeoDataFrame

from pg_data_etl import Database
from philly_transit_data import TransitData
from network_routing.database.setup.get_osm import import_osm_for_dvrpc_region


def explode_gdf_if_multipart(gdf: GeoDataFrame) -> GeoDataFrame:
    """Check if the geodataframe has multipart geometries.
    If so, explode them (but keep the index)
    """

    multipart = False

    for geom_type in gdf.geom_type.unique():
        if "Multi" in geom_type:
            multipart = True

    if multipart:
        gdf = gdf.explode()
        gdf["explode"] = gdf.index.to_numpy()
        gdf = gdf.reset_index()

    return gdf


def import_data_from_portal(db: Database):
    """Download starter data via public ArcGIS API using geopandas"""
    data_to_download = [
        (
            "Transportation",
            [
                "PassengerRailStations",
                "PedestrianNetwork_lines",
            ],
        ),
        ("Boundaries", ["MunicipalBoundaries"]),
    ]

    # Load each table up via mapserver URL

    for schema, table_list in data_to_download:
        for tbl in table_list:
            print("Importing", tbl)

            url = f"https://arcgis.dvrpc.org/portal/services/{schema}/{tbl}/MapServer/WFSServer?request=GetFeature&service=WFS&typename={tbl}&outputformat=GEOJSON&format_options=filename:{tbl.lower()}.geojson"

            gdf = gpd.read_file(url)

            gdf = explode_gdf_if_multipart(gdf)

            gdf = gdf.to_crs("EPSG:26918")

            sql_tablename = tbl.lower()

            db.import_geodataframe(gdf, sql_tablename, gpd_kwargs={"if_exists": "replace"})


def create_new_geodata(db: Database):
    """
    1) Merge DVRPC municipalities into counties
    2) Filter POIs to those within DVRPC counties
    """

    pa_counties = """
        ('Bucks', 'Chester', 'Delaware', 'Montgomery', 'Philadelphia')
    """
    nj_counties = "('Burlington', 'Camden', 'Gloucester', 'Mercer')"

    # Add regional county data
    regional_counties = f"""
        select co_name, state_name, (st_dump(st_union(geom))).geom
        from public.municipalboundaries m
        where (co_name in {pa_counties} and state_name ='Pennsylvania')
            or
            (co_name in {nj_counties} and state_name = 'New Jersey')
        group by co_name, state_name
    """
    db.gis_make_geotable_from_query(regional_counties, "regional_counties", "Polygon", 26918)


def setup_00_initial(local_db: Database):
    """Batch execute the entire process"""

    # 1) Import data from public ArcGIS Portal
    import_data_from_portal(local_db)

    # 2) Create new layers using what's already been imported
    create_new_geodata(local_db)

    # 3) Import all regional transit stops
    transit_data = TransitData()
    stops, lines = transit_data.all_spatial_data()

    stops = stops.to_crs("EPSG:26918")

    local_db.import_geodataframe(
        stops, "regional_transit_stops", gpd_kwargs={"if_exists": "replace"}
    )

    # 4) Import OSM data for the entire region
    import_osm_for_dvrpc_region(local_db, network_type="all")


if __name__ == "__main__":

    from network_routing import pg_db_connection

    db = pg_db_connection()

    setup_00_initial(db)

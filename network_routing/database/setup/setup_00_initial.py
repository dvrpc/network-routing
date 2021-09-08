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


# def import_production_sql_data(remote_db: Database, local_db: Database):
#     """Copy data from DVRPC's production SQL database to a SQL database on localhost.

#     NOTE: this connection will only work within the firewall.
#     """

#     data_to_download = [
#         (
#             "transportation",
#             ["pedestriannetwork_lines", "pedestriannetwork_points", "passengerrailstations"],
#         ),
#         ("structure", ["points_of_interest"]),
#         ("boundaries", ["municipalboundaries"]),
#         ("demographics", "ipd_2018"),
#     ]

#     for schema, table_list in data_to_download:

#         for table_name in table_list:

#             # Extract the data from the remote database
#             # and rename the geom column
#             query = f"SELECT * FROM {schema}.{table_name};"
#             gdf = remote_db.query_as_geo_df(query, geom_col="shape")
#             gdf = gdf.rename(columns={"shape": "geometry"}).set_geometry("geometry")

#             gdf = explode_gdf_if_multipart(gdf)

#             gdf = gdf.to_crs("EPSG:26918")

#             # Save to the local database
#             local_db.import_geodataframe(gdf, table_name.lower())


def import_data_from_portal(db: Database):
    """Download starter data via public ArcGIS API using geopandas"""
    data_to_download = [
        (
            "Transportation",
            [
                "PassengerRailStations",
                "PedestrianNetwork_lines",
                "PedestrianNetwork_points",
            ],
        ),
        ("Boundaries", ["MunicipalBoundaries"]),
        ("Demographics", ["IPD_2018"]),
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

            db.import_geodataframe(
                gdf, sql_tablename, gpd_kwargs={"if_exists": "replace"}
            )


def load_helper_functions(db: Database):
    """Add a SQL function to get a median()"""

    db.execute(
        """
        DROP FUNCTION IF EXISTS _final_median(anyarray);
        CREATE FUNCTION _final_median(anyarray) RETURNS float8 AS $$
        WITH q AS
        (
            SELECT val
            FROM unnest($1) val
            WHERE VAL IS NOT NULL
            ORDER BY 1
        ),
        cnt AS
        (
            SELECT COUNT(*) as c FROM q
        )
        SELECT AVG(val)::float8
        FROM
        (
            SELECT val FROM q
            LIMIT  2 - MOD((SELECT c FROM cnt), 2)
            OFFSET GREATEST(CEIL((SELECT c FROM cnt) / 2.0) - 1,0)
        ) q2;
        $$ LANGUAGE sql IMMUTABLE;

        CREATE AGGREGATE median(anyelement) (
        SFUNC=array_append,
        STYPE=anyarray,
        FINALFUNC=_final_median,
        INITCOND='{}'
        );
    """
    )


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
    db.gis_make_geotable_from_query(
        regional_counties, "regional_counties", "Polygon", 26918
    )


def setup_00_initial(local_db: Database):
    """Batch execute the entire process"""

    # if platform.system() in ["Linux", "Windows"] and "dvrpc.org" in socket.getfqdn():

    #     dvrpc_credentials = pGIS.configurations()["dvrpc_gis"]
    #     remote_db = PostgreSQL("gis", **dvrpc_credentials)

    #     # 1) Copy SQL data from production database
    #     import_production_sql_data(remote_db, local_db)

    # else:
    # 1b) Import data from public ArcGIS Portal
    import_data_from_portal(local_db)

    # 2) Load the MEDIAN() function into SQL
    load_helper_functions(local_db)

    # 3) Create new layers using what's already been imported
    create_new_geodata(local_db)

    # 4) Import all regional transit stops
    transit_data = TransitData()
    stops, lines = transit_data.all_spatial_data()

    stops = stops.to_crs("EPSG:26918")

    local_db.import_geodataframe(stops, "regional_transit_stops")

    # 5) Import OSM data for the entire region
    import_osm_for_dvrpc_region(local_db, network_type="all")


if __name__ == "__main__":

    from network_routing import pg_db_connection

    db = pg_db_connection()

    setup_00_initial(db)

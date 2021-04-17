import osmnx as ox

from postgis_helpers import PostgreSQL


def import_osm_for_dvrpc_region(db: PostgreSQL, network_type: str = "all"):
    """
    Import OpenStreetMap data to the database with osmnx.
    This bounding box overshoots the region and takes a bit to run.
    """

    print("-" * 80, "\nIMPORTING OpenStreetMap DATA")

    north, south, east, west = 40.601963, 39.478606, -73.885803, -76.210785

    print("\t -> Beginning to download...")
    G = ox.graph_from_bbox(north, south, east, west, network_type=network_type)
    print("\t -> ... download complete")

    # Force the graph to undirected, which removes duplicate edges
    print("\t -> Forcing graph to undirected edges")
    G = G.to_undirected()

    # Convert to geodataframes and save to DB
    print("\t -> Converting graph to geodataframes")
    nodes, edges = ox.graph_to_gdfs(G)

    db.import_geodataframe(edges, f"osm_edges_{network_type}")
    db.import_geodataframe(nodes, f"osm_nodes_{network_type}")

    # Reproject from 4326 to 26918 to facilitate analysis queries
    db.table_reproject_spatial_data(f"osm_edges_{network_type}", 4326, 26918, "LINESTRING")
    db.table_reproject_spatial_data(f"osm_nodes_{network_type}", 4326, 26918, "POINT")

    # Make a uuid column
    make_id_query = f"""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        alter table osm_edges_{network_type} add column osmuuid uuid;
        update osm_edges_{network_type} set osmuuid = uuid_generate_v4();
    """
    db.execute(make_id_query)
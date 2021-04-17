"""
Summary of ``clip_inputs.py``
-----------------------------

Use the table ``municipalboundaries`` to clip
out the sidewalk network within a buffer distance.
"""
from postgis_helpers import PostgreSQL


def clip_inputs(
    db: PostgreSQL, state: str, municipality: str = None, buffer_meters: float = None
):

    if state.upper() == "NJ":
        opposite_state = "Pennsylvania"
    else:
        opposite_state = "New Jersey"

    # Build up a SQL query that might buffer and/or include
    # a single municipality name
    if buffer_meters:
        place_query = f"SELECT st_union(st_buffer(geom, {buffer_meters})) "
    else:
        place_query = "SELECT st_union(geom) "

    place_query += f"""
        FROM public.municipalboundaries
        WHERE state = '{state.upper()}'
    """

    if municipality:
        place_query += f" AND UPPER(mun_label) = '{municipality.upper()}' "

    # Make a database schema for this clip
    if municipality:
        schema = municipality.lower().replace(" ", "_")
    else:
        schema = state.lower()

    db.execute(
        f"""
        DROP SCHEMA IF EXISTS {schema} CASCADE;
        CREATE SCHEMA {schema};
    """
    )

    data_to_clip = [
        ("pedestriannetwork_lines", "sidewalks", "LineString"),
        # ("regional_pois", "points_of_interest", "Point"),
        ("nodes_for_osm", "nodes_for_osm", "Point"),
        ("nodes_for_sidewalks", "nodes_for_sidewalks", "Point"),
        ("regional_transit_stops", "transit_stops", "Point"),
        ("osm_edges_drive", "osm_edges", "LineString"),
    ]

    for src_name, new_name, geom_type in data_to_clip:

        print(f"Clipping {src_name}")

        # Clip query will respect the buffer provided,
        # but will NOT include features from the 'opposite_state'

        clip_query = f"""
            SELECT * FROM public.{src_name} t
            WHERE ST_INTERSECTS(t.geom, ({place_query}))
                AND
             NOT ST_INTERSECTS(geom, (select st_collect(geom)
                                      from public.regional_counties
                                      where state_name = '{opposite_state}'))
        """
        db.make_geotable_from_query(
            clip_query, new_name, geom_type, 26918, schema=schema
        )

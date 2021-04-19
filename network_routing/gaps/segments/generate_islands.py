from tqdm import tqdm
from random import randint

from postgis_helpers import PostgreSQL


def _random_rgb(a: float = 1.0) -> str:
    """Generate a random RGB value, with an option for transparency

    Output is something like: 'rgba(5, 167, 230, 1.0)'
    """
    r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
    return f"rgba({r}, {g}, {b}, {a})"


def generate_islands(db: PostgreSQL, schema: str = None):
    """Use the sidewalk layer to merge intersecting geometries.
    The output is a layer with one feature per 'island'
    It also has a column for size of island and a randomly-generated RGB value.
    """

    full_table_name = "pedestriannetwork_lines" if not schema else f"{schema}.sidewalks"
    output_schema = "data_viz" if not schema else schema

    db.execute(
        f"""
        CREATE SCHEMA IF NOT EXISTS {output_schema};
    """
    )

    query = f"""
        SELECT
            ST_COLLECTIONEXTRACT(
                UNNEST(ST_CLUSTERINTERSECTING(geom)),
                2
            ) AS geom
        FROM {full_table_name}
    """
    db.make_geotable_from_query(query, "islands", "MULTILINESTRING", 26918, schema=output_schema)

    # Add a column for size
    db.table_add_or_nullify_column("islands", "size_miles", "FLOAT", schema=output_schema)

    query = f"UPDATE {output_schema}.islands SET size_miles = ST_LENGTH(geom) * 0.000621371;"
    db.execute(query)

    # Add columns for rgba and muni names
    for colname in ["rgba", "muni_names"]:
        db.table_add_or_nullify_column("islands", colname, "TEXT", schema=output_schema)

    db.table_add_or_nullify_column("islands", "muni_count", "FLOAT", schema=output_schema)

    # Iterate over each feature. Make a random rgb code and find intersecting municipalities
    query = f"SELECT uid FROM {output_schema}.islands"
    uids = db.query_as_df(query)
    for idx, row in tqdm(uids.iterrows(), total=uids.shape[0]):
        # print(row.uid)

        # Query the intersecting municipalities
        query = f"""
            SELECT
                mun_name,
                st_length(st_intersection(i.geom, m.geom)) / st_length(i.geom) * 100 as pct_covered
            FROM
                municipalboundaries m,
                data_viz.islands i
            WHERE
                    st_intersects(m.geom, i.geom)
                AND
                    i.uid = {row.uid}
            ORDER BY
                pct_covered DESC
        """
        munis = db.query_as_list(query)

        # Record the muni names and the percent covered
        result = ""
        for muni_name, pct_covered in munis:
            result += f"{muni_name}: {round(pct_covered, 1)},"

        update = f"""
            UPDATE {output_schema}.islands
            SET
                muni_names = '{result}',
                muni_count = {len(munis)},
                rgba = '{_random_rgb()}'
            WHERE
                uid = {row.uid}
        """
        db.execute(update)

    # Generate a set of concave hulls around the islands
    _generate_island_hulls(db)


def _generate_island_hulls(db: PostgreSQL):
    """
    Turn the linear island layer into a polygon-shaped concave hull layer
    """
    query = f"""
        select
            uid as island_id,
            size_miles,
            rgba,
            muni_names,
            muni_count,
            st_concavehull(st_buffer(geom, 7.5), 0.8) as geom
	    from
            data_viz.islands
    """
    db.make_geotable_from_query(query, "island_hulls", "POLYGON", 26918, schema="data_viz")


if __name__ == "__main__":
    from network_routing import db_connection

    db = db_connection()
    _generate_island_hulls(db)

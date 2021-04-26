from tqdm import tqdm
from random import randint

from postgis_helpers import PostgreSQL


def random_rgb(a: float = 1.0) -> str:
    """
    - Generate a random RGB value, with an option for transparency. This is used to
    assign a unique RGB value to each island.

    Args:
        a (float): transparency value

    Returns:
        something like `'rgba(5, 167, 230, 1.0)'`

    """
    r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
    return f"rgba({r}, {g}, {b}, {a})"


def generate_islands(db: PostgreSQL, tbl: str = "pedestriannetwork_lines"):
    """
    Merge intersecting sidewalk geometries to create "islands" of connectivity.

    The output is a layer with one feature per 'island', and has a column for size of island and a randomly-generated RGB value.

    Args:
        db (PostgreSQL): analysis database
        tbl (str): name of the table to analyze

    """

    output_schema = "data_viz"

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
        FROM {tbl}
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
                rgba = '{random_rgb()}'
            WHERE
                uid = {row.uid}
        """
        db.execute(update)


if __name__ == "__main__":
    from network_routing import db_connection

    db = db_connection()
    generate_islands(db)

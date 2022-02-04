from tqdm import tqdm
from random import randint

from pg_data_etl import Database


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


def generate_islands(db: Database, tbl: str = "pedestriannetwork_lines"):
    """
    Merge intersecting sidewalk geometries to create "islands" of connectivity.

    The output is a layer with one feature per 'island', and has a column for size of island and a randomly-generated RGB value.

    Args:
        db (Database): analysis database
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
    db.gis_make_geotable_from_query(query, f"{output_schema}.islands", "MULTILINESTRING", 26918)

    # Add a column for size
    db.execute(
        f"""
        ALTER TABLE {output_schema}.islands
        ADD COLUMN size_miles FLOAT;
    """
    )

    db.execute(
        f"""
        UPDATE {output_schema}.islands 
        SET size_miles = ST_LENGTH(geom) * 0.000621371;
    """
    )

    # Add columns for rgba and muni names
    for colname in ["rgba", "muni_names"]:
        db.execute(
            f"""
            ALTER TABLE {output_schema}.islands
            ADD COLUMN {colname} TEXT;
        """
        )

    db.execute(
        f"""
        ALTER TABLE {output_schema}.islands
        ADD COLUMN muni_count FLOAT;
    """
    )

    # Iterate over each feature. Make a random rgb code and find intersecting municipalities
    query = f"SELECT uid FROM {output_schema}.islands"
    uids = db.df(query)
    for idx, row in tqdm(uids.iterrows(), total=uids.shape[0]):

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
        munis = db.query_as_list_of_lists(query)

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
    from network_routing import pg_db_connection

    db = pg_db_connection()
    generate_islands(db)

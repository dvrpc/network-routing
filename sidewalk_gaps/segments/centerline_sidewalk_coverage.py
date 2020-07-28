from tqdm import tqdm

from postgis_helpers import PostgreSQL
from sidewalk_gaps import CREDENTIALS

database_name = "sidewalk_gaps"


if __name__ == "__main__":
    db = PostgreSQL(
        database_name,
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )

    tbl = "nj_centerline"

    # Define the column to populate
    new_col = "sidewalk_3"

    # Get a list of all centerlines we want to iterate over.
    # Omit 100 and 200 level highways
    oid_query = f"""
        SELECT objectid FROM {tbl}
        WHERE symboltype >= 300
    """

    db.table_add_or_nullify_column(tbl, new_col, "FLOAT")

    # Check if the new_col exists.
    # If so, iterate over null features
    df = db.query_as_df(f"SELECT * FROM {tbl} LIMIT 1")
    if new_col in df.columns:
        oid_query += f"""
            AND {new_col} IS NULL
        """
    # Otherwise, make the column and operate on the entire dataset
    else:
        db.table_add_or_nullify_column(tbl, new_col, "FLOAT")

    # Hit the database
    oid_list = db.query_as_list(oid_query)

    # pop the results out of tuples into a simple list
    oid_list = [x[0] for x in oid_list]

    query_template = """
        SELECT
            SUM(
                ST_LENGTH(
                    ST_INTERSECTION(sw.geom, (SELECT ST_BUFFER(c.geom,25)))
                )
            )
        FROM
            pedestriannetwork_lines sw, nj_centerline c
        where
            c.objectid = OID_PLACEHOLDER
            AND
            ST_INTERSECTS(sw.geom, (SELECT ST_BUFFER(c.geom,25)))
            AND
                sw.line_type = 1
            AND
                (
                    ST_LENGTH(
                        ST_INTERSECTION(sw.geom, (SELECT ST_BUFFER(c.geom,25)))
                    ) > 25
                    OR ST_LENGTH(sw.geom) <= 25
                )
    """
    for oid in tqdm(oid_list, total=len(oid_list)):
        oid_query = query_template.replace("OID_PLACEHOLDER", str(oid))

        sidwalk_length_in_meters = db.query_as_single_item(oid_query)

        if not sidwalk_length_in_meters:
            sidwalk_length_in_meters = 0

        update_query = f"""
            UPDATE {tbl} c
            SET {new_col} = {sidwalk_length_in_meters}
            WHERE objectid = {oid}
        """
        db.execute(update_query)



    # parallel_template = """
    #     SELECT
    #         SUM(
    #             ST_LENGTH(
    #                 ST_INTERSECTION(sw.geom, (SELECT ST_BUFFER(c.geom,25)))
    #             )
    #         )
    #     FROM
    #         pedestriannetwork_lines sw, nj_centerline c
    #     where
    #         c.objectid = OID_PLACEHOLDER
    #         AND
    #         ST_INTERSECTS(sw.geom, (SELECT ST_BUFFER(c.geom,25)))
    #         AND
    #             sw.line_type = 1
    #         AND (
    #             (degrees(st_angle(st_intersection(sw.geom, (SELECT ST_BUFFER(c.geom,25))), c.geom)) between 135 and 225)
    #             OR
    #             (degrees(st_angle(st_intersection(sw.geom, (SELECT ST_BUFFER(c.geom,25))), c.geom)) <= 45)
    #             OR
    #             (degrees(st_angle(st_intersection(sw.geom, (SELECT ST_BUFFER(c.geom,25))), c.geom)) >= 315)
    #         )
    # """



    # query_template = f"""
    #     SELECT
    #         SUM(
    #             ST_LENGTH(
    #                 ST_INTERSECTION(pl.geom, ({inner_subquery}))
    #             )
    #         ) AS sidewalk_length
    #     FROM
    #         pedestriannetwork_lines pl
    #     WHERE
    #         ST_INTERSECTS(pl.geom, ({inner_subquery}))
    #         AND
    #             pl.line_type = 1
    # """
    #     # update_query = f"""
    #     #     UPDATE nj_centerline c
    #     #     SET sidewalk_meters = (
    #     #         SELECT SUM(
    #     #             ST_LENGTH(
    #     #                 ST_INTERSECTION(
    #     #                     s.geom, (SELECT st_buffer(c.geom, 25))
    #     #                 )
    #     #             )
    #     #         )
    #     #         FROM pedestriannetwork_lines s
    #     #         WHERE
    #     #                 ST_INTERSECTS(
    #     #                     ST_CENTROID(s.geom), (SELECT st_buffer(c.geom, 25))
    #     #                 )
    #     #             AND
    #     #                 s.line_type = 1
    #     #     )
    #     #     WHERE c.objectid = {oid}
    #     # """

    #     # db.execute(update_query)



    # query_to_compare_angles = """
    #     select degrees(st_angle(s.geom, c.geom))
    #     from pedestriannetwork_lines s, nj_centerline c
    #     where s.uid = 135049 and c.objectid = 2124
    # """

    # # Refined query that attempts to account for parallelness
    # parallel_query = """

    #     select
    #         sum(
    #             ST_LENGTH(
    #                 ST_INTERSECTION(pl.geom, (SELECT ST_BUFFER(c.geom,25)))
    #             )
    #         )
    #     FROM
    #         pedestriannetwork_lines pl, nj_centerline c
    #     where
    #         c.objectid = 2124
    #         AND
    #         ST_INTERSECTS(pl.geom, (SELECT ST_BUFFER(c.geom,25)))
    #         AND
    #             pl.line_type = 1
    #             and (
    #             (degrees(st_angle(st_intersection(pl.geom, (SELECT ST_BUFFER(c.geom,25))), c.geom)) between 135 and 225)
    #             or
    #             (degrees(st_angle(st_intersection(pl.geom, (SELECT ST_BUFFER(c.geom,25))), c.geom)) <= 45)
    #             or
    #             (degrees(st_angle(st_intersection(pl.geom, (SELECT ST_BUFFER(c.geom,25))), c.geom)) >= 315)
    #         )

    # """
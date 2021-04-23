"""

"""

from tqdm import tqdm

from postgis_helpers import PostgreSQL


def classify_centerlines(db: PostgreSQL, schema: str, tbl: str, new_col: str = "sidewalk"):
    """
    `classify_centerlines()` evaluates a centerline dataset against a sidewalk dataset.

    Using a search distance of 25 meters, it identifies the sum of the lengths of all sidewalk segments that:

    1. is `line_type=1`
    2. intersection is more than 25 meters or the segment itself is less than 25 meters

    As it runs, it creates `new_col` within `schema`.`tbl` and updates the table in-place.

    Args:
        db (PostgreSQL): analysis database
        schema (str): schema where source data can be found
        tbl (str): name of the centerline table to analyze
        new_col (str): name of the new `FLOAT` column where data will be stored.
    """

    # Add a column to filter out features we don't want to classify
    if "analyze_sw" not in db.table_columns_as_list(tbl, schema=schema):

        db.table_add_or_nullify_column(tbl, "analyze_sw", "INT", schema=schema)

        db.execute(
            f"""
            UPDATE {schema}.{tbl}
            SET analyze_sw = 1;
        """
        )
        db.execute(
            f"""
            UPDATE {schema}.{tbl}
            SET analyze_sw = 0
            WHERE highway LIKE '%%bridleway%%' 
                OR highway LIKE '%%bus_guideway%%' 
                OR highway LIKE '%%bus_stop%%' 
                OR highway LIKE '%%busway%%' 
                OR highway LIKE '%%cycleway%%' 
                OR highway LIKE '%%footway%%' 
                OR highway LIKE '%%path%%' 
                OR highway LIKE '%%pedestrian%%' 
                OR highway LIKE '%%service%%' 
                OR highway LIKE '%%track%%' 
                OR highway LIKE '%%steps%%';
        """
        )

    # Get a list of all centerlines we want to iterate over.
    oid_query = f"""
        SELECT uid FROM {schema}.{tbl} WHERE analyze_sw = 1
    """

    # But first...  check if the new_col exists
    # If so, iterate over null features
    # Otherwise, make the column and operate on the entire dataset

    column_already_existed = new_col in db.table_columns_as_list(tbl, schema=schema)

    if column_already_existed:
        print("Picking up where last left off...")
        oid_query += f"""
            AND {new_col} IS NULL
        """
    else:
        print("Analyzing for the first time...")
        db.table_add_or_nullify_column(tbl, new_col, "FLOAT", schema=schema)

    # Hit the database
    oid_list = db.query_as_list(oid_query)

    # pop the results out of tuples into a simple list
    oid_list = [x[0] for x in oid_list]

    query_template = f"""
        SELECT
            SUM(
                ST_LENGTH(
                    ST_INTERSECTION(sw.geom, (SELECT ST_BUFFER(c.geom,25)))
                )
            )
        FROM
            {schema}.pedestriannetwork_lines sw, {schema}.{tbl} c
        where
            c.uid = OID_PLACEHOLDER
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
            UPDATE {schema}.{tbl} c
            SET {new_col} = {sidwalk_length_in_meters}
            WHERE uid = {oid}
        """
        db.execute(update_query)


if __name__ == "__main__":
    pass

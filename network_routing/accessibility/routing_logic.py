from pg_data_etl import Database


def get_unique_ids(db: Database, table: str, column: str) -> dict:
    """
    Return a dictionary with each unique value within the `column` of `table`
    These could be text values or numeric.

    These values are all sanitized with the following characters removed:
        space, slash, dash, comma

    Arguments:
        db (Database): analysis postgresql database
        table (str): name of the table to extract values from
        column (str): name of the column within `table` that has values

    Returns:
        dict: where the key is the raw text from SQL, value is the santinized version

        {"Food/Drink": "fooddrink",
            "Library"   : "library",}

    """
    id_query = f"""
        SELECT distinct {column}::text
        FROM {table}
    """
    all_ids = db.query_as_list_of_singletons(id_query)

    id_dict = {x: x for x in all_ids}

    bad_characters = [" ", r"/", "-", ","]

    for single_id in id_dict:

        nice_id = single_id.lower()

        for char in bad_characters:
            nice_id = nice_id.replace(char, "")

        id_dict[single_id] = nice_id

    return id_dict


def assign_node_ids_to_network(
    db: Database, edge_table_name: str, node_table_name: str, node_id_column: str
) -> None:
    """
    - Starting with an edge table and companion node table, this function
    adds `start_id` and `end_id` columns to the edge table and populates each
    record with the ID of the node at the start and end of the segment

    Arguments:
        db (Database): analysis postgresql database
        edge_table_name (str): name of the edge table
        node_table_name (str): name of the companion node table
        node_id_column (str): name of the unique ID column in the node table

    Returns:
        None: but updates the `edge_table_name` in-place with new columns and values within
    """

    print("Assigning Node ID values to the edge table")

    # Add columns for the start and end node_id values
    for column_name in ["start_id", "end_id"]:
        query = f"""
            ALTER TABLE {edge_table_name}
            ADD COLUMN {column_name} INT;
        """
        db.execute(query)

    # Execute the query for the START of each segment
    start_id_query = f"""
        UPDATE {edge_table_name} ln
        SET start_id = (
            SELECT pt.{node_id_column}
            FROM {node_table_name} pt
            WHERE 
                ST_DWITHIN(
                    pt.geom,
                    st_startpoint(ln.geom),
                    5
                )
            ORDER BY
                ST_DISTANCE(
                    pt.geom,
                    st_startpoint(ln.geom)
                )
                ASC LIMIT 1
        )
    """
    db.execute(start_id_query)

    # Execute the query for the END of each segment
    end_id_query = start_id_query.replace("start", "end")
    db.execute(end_id_query)


#
def add_travel_time_weights_to_network(
    db: Database, edge_table_name: str, walking_mph: float = 2.5
):
    """
    Add impedence columns to the edges.

        1) Calculate the legnth in meters (epsg:26918)
        2) Convert meters into minutes:
            - divide by 1609.34
            - divide by defined walking speed in MPH
            - multiply by 60 to get minutes
    """

    print(f"Adding travel time weights to {edge_table_name}")

    # Add a meter length and minutes column
    for column_name in ["len_meters", "minutes"]:
        query = f"""
            ALTER TABLE {edge_table_name}
            ADD COLUMN {column_name} FLOAT;
        """
        db.execute(query)

    # Capture length in meters into its own column
    update_meters = f"""
        UPDATE {edge_table_name}
        SET len_meters = ST_LENGTH(geom);
    """
    db.execute(update_meters)

    # Calculate walking travel time in minutes
    update_minutes = f"""
        UPDATE {edge_table_name}
        SET minutes = len_meters / 1609.34 / {walking_mph} * 60;
    """
    db.execute(update_minutes)

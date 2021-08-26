from __future__ import annotations
import pandana as pdna
from pathlib import Path

from pg_data_etl import Database


def sanitize_single_id(value: str | int) -> str:
    """
    Update `value` to a sanitized sql-friendly name.
    Force to string and then scrub out: space, slash, dash, comma

    e.g. "Food/Drink" -> "fooddrink"

    Arguments:
        value (str | int): unique ID value for a POI

    Returns:
        str: POI value that works in SQL
    """
    bad_characters = [" ", r"/", "-", ","]

    v = str(value).lower()

    for char in bad_characters:
        v = v.replace(char, "")

    return v


def get_unique_ids(db: Database, table: str, column: str) -> dict:
    """
    Return a dictionary with each unique value within the `column` of `table`
    These could be text values or numeric.

    Key is original value, value is the sanitized version.

    Arguments:
        db (Database): analysis postgresql database
        table (str): name of the table to extract values from
        column (str): name of the column within `table` that has values

    Returns:
        dict: where the key is the raw text from SQL, value is the santinized version

    """
    id_query = f"""
        SELECT distinct {column}::text
        FROM {table}
    """
    all_ids = db.query_as_list_of_singletons(id_query)

    id_dict = {x: x for x in all_ids}

    for single_id in id_dict:

        id_dict[single_id] = sanitize_single_id(single_id)

    return id_dict


def analyze_single_poi(
    db: Database,
    network: pdna.Network,
    poi_uid: int | str,
    poi_table_name: str,
    poi_id_column: str,
    edge_table_name: str,
    poi_match_threshold: float,
    max_minutes: float,
    num_pois: int,
    write_to_csv: bool = False,
) -> None:

    clean_id = sanitize_single_id(poi_uid)

    # Check that output table doesn't exist yet if writing to CSV
    # If it exists, alert the user and do not compute this POI!

    if write_to_csv:
        output_path = Path("./data") / f"{edge_table_name}_{clean_id}.csv"
        if output_path.exists():
            print(f"{output_path=} already exists! Skipping...")
            return None, None

    # Get all POIs with this uid
    # that are within 'poi_match_threshold' meters of a sidewalk
    poi_query = f"""
        SELECT *,
            ST_X(st_transform(geom, 4326)) as x,
            ST_Y(st_transform(geom, 4326)) as y
        FROM {poi_table_name}
        WHERE {poi_id_column}::text = '{poi_uid}'
        AND ST_DWITHIN(
            geom,
            (SELECT ST_COLLECT(geom) FROM {edge_table_name}),
            {poi_match_threshold}
        )
    """
    poi_gdf = db.gdf(poi_query)

    # If there aren't any rows in the query result,
    # there are no POIs with this ID that are 'close enough'
    # to the sidewalk network.
    # Break out of function early if this happens.
    if poi_gdf.shape[0] == 0:
        return None, None

    # Assign the POIs to the network
    network.set_pois(
        category=clean_id,
        x_col=poi_gdf["x"],
        y_col=poi_gdf["y"],
        maxdist=max_minutes,
        maxitems=num_pois,
    )

    # Calculate the distance across the network to this set of POIs
    df = network.nearest_pois(distance=max_minutes, category=clean_id, num_pois=num_pois)

    # Clean up the column names into something distinct
    # i.e. '1' turns into 'n_1_ID' for a given ID, etc.
    new_colnames = {}
    n1 = None
    for column in df.columns:

        # CSV output does not need the ID as a column name suffix
        if write_to_csv:
            new_name = f"n_{column}"

        # If merging with other results, we need the POI ID in the column name
        else:
            new_name = f"n_{column}_{clean_id}"

        new_colnames[column] = new_name

        if int(column) == 1:
            n1 = new_name

    df = df.rename(index=str, columns=new_colnames)

    # Filter results to values below max threshold
    # defaults to the closest (n = 1)
    df = df[df[n1] < max_minutes]

    if write_to_csv:
        df.to_csv(output_path)

    return poi_gdf, df

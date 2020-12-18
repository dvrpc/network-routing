from postgis_helpers import PostgreSQL


def cleanup_outputs(
    db: PostgreSQL,
    analysis_schema: str,
    poi_id_column: str,
    new_schema: str,
    tables_to_move: list,
):
    """ Move results to new schema and merge all tables prefixed with 'poi_' """

    schema_query = f"""
        DROP SCHEMA IF EXISTS {new_schema} CASCADE;
        CREATE SCHEMA {new_schema};
    """

    db.execute(schema_query)

    for table in tables_to_move:
        move_schema_query = f"""
            ALTER TABLE {analysis_schema}.{table}
            SET SCHEMA {new_schema};
        """
        db.execute(move_schema_query)

    qa_tables = [x for x in db.all_spatial_tables_as_dict() if "poi_" in x]

    if len(qa_tables) >= 2:

        qa_subqueries = [
            f"SELECT {poi_id_column}, geom FROM {analysis_schema}.{x}"
            for x in qa_tables
        ]

        query = """
            UNION
        """.join(
            qa_subqueries
        )

        db.make_geotable_from_query(
            query, "qaqc_node_match", "LINESTRING", 26918, schema=new_schema
        )

    for qa_table in qa_tables:
        db.table_delete(qa_table, schema=analysis_schema)


if __name__ == "__main__":
    from helpers import db_connection

    db = db_connection()
    cleanup_outputs(
        db, "nj", "src", "transit_gaps", ["all_transit_results", "all_transit_table"]
    )

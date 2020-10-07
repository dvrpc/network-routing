from postgis_helpers import PostgreSQL


def generate_sidewalk_nodes(db: PostgreSQL,
                            sw_tbl: str = "pedestriannetwork_lines"):

    # Query out all unique nodes, then save result to database
    # --------------------------------------------------------

    node_query = f"""
        SELECT st_startpoint(geom) AS geom
        FROM public.{sw_tbl}
        UNION
        SELECT st_endpoint(geom) AS geom
        FROM public.{sw_tbl}
        GROUP BY geom
    """

    kwargs = {
        "new_table_name": "sw_nodes",
        "geom_type": "Point",
        "epsg": 26918,
        "uid_col": "sw_node_id",
    }

    db.make_geotable_from_query(node_query, **kwargs)


if __name__ == "__main__":
    from sidewalk_gaps import CREDENTIALS

    schema = "camden"

    db = PostgreSQL(
        "sidewalk_gaps",
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )

    generate_sidewalk_nodes(db)

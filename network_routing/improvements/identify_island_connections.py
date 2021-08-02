from network_routing import pg_db_connection


query_template = """
    with main_geom as (
        select geom
        from improvements.montgomery_split ms 
        where uid = ID_PLACEHOLDER
    ),
    connector_geoms as (
        select t.geom
        from
            improvements.montgomery_connectors t,
            main_geom
        where st_intersects(t.geom, main_geom.geom)
    ),
    merged_geoms as (
        select geom from main_geom
        union
        select geom from connector_geoms
    ),
    collected_geoms as (
        select st_collect(geom) as geom
        from merged_geoms
    )
    select count(i.uid)
    from
        data_viz.islands i,
        collected_geoms g
    where st_intersects(i.geom, g.geom)
"""


if __name__ == "__main__":
    db = pg_db_connection()

    uids = db.query_as_list_of_singletons("SELECT uid FROM improvements.montgomery_split")

    for uid in uids:
        query = query_template.replace("ID_PLACEHOLDER", str(uid))

        print(query)

        result = db.query_as_singleton(query)

        print(uid, result)

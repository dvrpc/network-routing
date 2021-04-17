import pandas as pd
from tqdm import tqdm
from postgis_helpers import PostgreSQL


def hexagon_summary(db: PostgreSQL):

    db.make_hexagon_overlay("hexagons", "regional_counties", 26918, 3)

    for colname in ["islands", "poi_min", "poi_median", "poi_max", "cl_len", "sw_len"]:
        db.table_add_or_nullify_column("hexagons", colname, "FLOAT")

    for state, schema in [("New Jersey", "nj"), ("Pennsylvania", "pa")]:

        print(f"Processing {state}")

        hex_query = f"""
            SELECT *
            FROM hexagons
            WHERE
                st_intersects(
                    st_centroid(geom),
                    (select st_collect(geom)
                    from regional_counties
                    where state_name = '{state}'
                    )
                )
        """
        db.make_geotable_from_query(
            hex_query, "hexagon_summary", "POLYGON", 26918, schema=schema
        )

        uid_query = f"""
            SELECT uid FROM {schema}.hexagon_summary
        """
        uid_list = db.query_as_list(uid_query)

        for uid in tqdm(uid_list, total=len(uid_list)):
            uid = uid[0]

            geom_subquery = (
                f"select geom from {schema}.hexagon_summary where uid = {uid}"
            )

            # Get the number of islands
            # -------------------------

            island_update = f"""
                update {schema}.hexagon_summary h
                set islands = (
                    select count(island_geom) from (
                        SELECT
                            ST_COLLECTIONEXTRACT(
                                UNNEST(ST_CLUSTERINTERSECTING(geom)),
                                2
                            ) AS geom
                        FROM {schema}.sidewalks sw
                        where st_within(sw.geom, h.geom)
                    ) as island_geom
                )
                where h.uid = {uid}
            """
            db.execute(island_update)

            # Get the min and max distance to nearest school
            # ----------------------------------------------
            q_network = f"""
                select
                    min(n_1_school),
                    median(n_1_school),
                    max(n_1_school)
                from {schema}.access_results
                where
                    n_1_school < 180
                and
                    st_intersects(
                        geom,
                        ({geom_subquery})
                    )
            """
            poi_result = db.query_as_list(q_network)
            poi_min, poi_med, poi_max = poi_result[0]

            # # Replace "None" values with a dummy number
            if str(poi_min) == "None":
                poi_min = "NULL"
            if str(poi_med) == "None":
                poi_med = "NULL"
            if str(poi_max) == "None":
                poi_max = "NULL"

            # Get the centerline length
            # -------------------------
            cl_query = f"""
                select
                    sum(st_length(st_intersection(
                                        geom,
                                        ({geom_subquery})
                        ))) as cl_len
                from {schema}.centerlines
                where st_intersects(geom, ({geom_subquery}))
            """
            cl_results = db.query_as_list(cl_query)
            cl_len = cl_results[0][0]

            if str(cl_len) == "None":
                cl_len = 0

            # Get the sidewalk length
            # -------------------------
            sw_query = f"""
                select
                    sum(st_length(st_intersection(
                                        geom,
                                        ({geom_subquery})
                        ))) as sw_len
                from {schema}.sidewalks
                where st_intersects(geom, ({geom_subquery}))
            """
            sw_results = db.query_as_list(sw_query)
            sw_len = sw_results[0][0]

            if str(sw_len) == "None":
                sw_len = 0

            # Update the table with the results
            # ---------------------------------
            update_query = f"""
                UPDATE {schema}.hexagon_summary
                SET poi_min = {poi_min},
                    poi_median = {poi_med},
                    poi_max = {poi_max},
                    cl_len = {cl_len},
                    sw_len = {sw_len}
                WHERE uid = {uid}
            """
            db.execute(update_query)

    # Combine state-specific hexagons into one final summary layer
    # ------------------------------------------------------------

    query = """
        SELECT * FROM nj.hexagon_summary
        UNION
        SELECT * FROM pa.hexagon_summary
    """
    db.make_geotable_from_query(query, "hexagon_summary", "POLYGON", 26918)


def classify_hex_results(db: PostgreSQL):

    # Classify the hexagon results into two columns:
    # 1) Can the SW network be expanded to streets w/out SWs?
    # 2) Can the existing SW network be better connected to itself?

    # Streets without sidewalks
    # Classify those that have roadways but NO sidewalks

    db.table_add_or_nullify_column("hexagon_summary", "growth", "TEXT")
    db.table_add_or_nullify_column("hexagon_summary", "connectivity", "TEXT")

    growth_breakpoint_1 = 0.1
    growth_breakpoint_2 = 0.8

    sql_growth = f"""
        UPDATE hexagon_summary
        SET growth = CASE
            WHEN cl_len  > 0
                 and
                 sw_len / cl_len  <= {growth_breakpoint_1}
                THEN 'Few Sidewalks'

            WHEN cl_len  > 0
                 and
                 sw_len > 0
                 and
                 sw_len / cl_len  > {growth_breakpoint_1}
                 and
                 sw_len / cl_len  <= {growth_breakpoint_2}
                THEN 'Some Sidewalks'

            WHEN cl_len  > 0
                 and
                 sw_len > 0
                 and
                 sw_len / cl_len  > {growth_breakpoint_2}
                THEN 'Many Sidewalks'

            ELSE NULL
        END
    """
    db.execute(sql_growth)


if __name__ == "__main__":
    from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME

    db = PostgreSQL(PROJECT_DB_NAME, **CREDENTIALS["localhost"])

    combine_transit_results(db)

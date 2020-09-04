from tqdm import tqdm
from postgis_helpers import PostgreSQL


def hexagon_summary(db: PostgreSQL):

    db.make_hexagon_overlay("hexagons", "regional_counties", 26918, 3)

    for colname in ["islands", "poi_min", "poi_median", "poi_max", "cl_len", "sw_len"]:
        db.table_add_or_nullify_column("hexagons", colname, "FLOAT")

    for state, schema in [("New Jersey", "nj"),
                          ("Pennsylvania", "pa")]:

        print(f"Processing {state}")

        hex_query = f"""
            SELECT *
            FROM hexagons
            WHERE
                st_intersects(
                    geom,
                    (select st_collect(geom)
                    from regional_counties
                    where state_name = '{state}'
                    )
                )
        """
        db.make_geotable_from_query(hex_query, "hexagon_summary", "POLYGON", 26918, schema=schema)

        uid_query = f"""
            SELECT uid FROM {schema}.hexagon_summary
        """
        uid_list = db.query_as_list(uid_query)

        for uid in tqdm(uid_list, total=len(uid_list)):
            uid = uid[0]

            geom_subquery = f"select geom from {schema}.hexagon_summary where uid = {uid}"

            # Get the number of islands
            # -------------------------
            q_island = f"""
                select count(uid)
                from {schema}.islands
                where st_intersects(
                    geom,
                    ({geom_subquery})
                )
            """
            num_islands = db.query_as_single_item(q_island)

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

            # Replace "None" values with a dummy number
            if not poi_min:
                poi_min = 999
            if not poi_med:
                poi_med = 999
            if not poi_max:
                poi_max = 999

            # Get the centerline and sidewalk lengths
            # ---------------------------------------
            cl_query = f"""
                select
                    sum(st_length(st_intersection(
                                        geom,
                                        ({geom_subquery})
                        ))) as cl_len,
                    sum(st_length(st_intersection(
                                        geom,
                                        ({geom_subquery})
                        )) / st_length(geom) * sidewalk) as sw_len
                from {schema}.centerlines
                where st_intersects(geom, ({geom_subquery}))
            """
            cl_results = db.query_as_list(cl_query)
            cl_len, sw_len = cl_results[0]

            if not cl_len:
                cl_len = 0
            if not sw_len:
                sw_len = 0

            # Update the table with the results
            # ---------------------------------
            update_query = f"""
                UPDATE {schema}.hexagon_summary
                SET islands = {num_islands},
                    poi_min = {poi_min},
                    poi_median = {poi_med},
                    poi_max = {poi_max},
                    cl_len = {cl_len},
                    sw_len = {sw_len}
                WHERE uid = {uid}
            """
            db.execute(update_query)

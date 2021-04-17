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

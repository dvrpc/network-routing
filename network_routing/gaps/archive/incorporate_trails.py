from tqdm import tqdm
from postgis_helpers import PostgreSQL


def prepare_trail_data(db: PostgreSQL):

    # Filter down to only the existing trails
    # ---------------------------------------

    trail_query = " SELECT * FROM circuittrails WHERE circuit = 'Existing' "

    db.make_geotable_from_query(
        trail_query, "existing_trails", geom_type="LINESTRING", epsg=26918
    )

    # Figure out if each segment should be included
    # ---------------------------------------------

    db.table_add_or_nullify_column("existing_trails", "sw_coverage", "FLOAT")

    uid_list = db.query_as_list("SELECT uid FROM existing_trails")

    # Template to get the % covered by sidewalk features
    query_template = """
        select
            sum(
                st_length(
                    st_intersection(geom, (select st_buffer(geom, 10)
                                           from existing_trails
                                           where uid = UID)
                    )
                )
            ) / (select st_length(geom) from existing_trails where uid = UID)
        from
            pedestriannetwork_lines
        where
            st_dwithin(
                st_startpoint(geom),
                (select geom from existing_trails where uid = UID),
                10
            )
        or
            st_dwithin(
                st_endpoint(geom),
                (select geom from existing_trails where uid = UID),
                10
            )
    """

    for uid in tqdm(uid_list, total=len(uid_list)):
        uid = uid[0]
        query = query_template.replace("UID", str(uid))
        result = db.query_as_single_item(query)

        if not result:
            result = 0

        update_query = f"""
            UPDATE existing_trails
            SET sw_coverage = {result}
            WHERE uid = {uid};
        """
        db.execute(update_query)


if __name__ == "__main__":
    from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME

    db = PostgreSQL(PROJECT_DB_NAME, verbosity="minimal", **CREDENTIALS["localhost"])

    prepare_trail_data(db)

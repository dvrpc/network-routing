"""
This script merges the sidewalk line geometries and CircuitTrails layers
into a single topologically-sound layer. It requires splitting segments
within each layer wherever there is an intersection between the two layers.
"""
from postgis_helpers import PostgreSQL


def add_segmentation_to_trails(db: PostgreSQL):
    """ Split the trail layer wherever it intersects a sidewalk """

    # Make a filtered version of the trail data that pedestrians can use
    # ------------------------------------------------------------------

    trail_query = """
        SELECT * FROM circuittrails
        WHERE
                circuit = 'Existing'
            AND
                (facility NOT LIKE '%%Bicycle%%' OR facility IS NULL);
    """

    db.make_geotable_from_query(
        trail_query, "ped_trails", geom_type="LINESTRING", epsg=26918
    )

    # Split the trails wherever they intersect a sidwalk
    # --------------------------------------------------

    trail_split = """
        select
            globalid,
            (st_dump(
                st_split(
                    t1.geom,
                    (select st_collect(geom)
                    from pedestriannetwork_lines p1
                    where st_intersects(t1.geom, p1.geom)
                    )
                )
            )).geom
        from ped_trails t1
    """
    db.make_geotable_from_query(
        trail_split, "trail_splits", geom_type="LINESTRING", epsg=26918
    )

    # Merge the split trails with any trails that didn't get split
    # ------------------------------------------------------------

    trail_merge = """
        select
            'trail - raw' as src,
            geom
        from ped_trails
        where
            not st_within(geom, (select st_buffer(st_collect(geom), 1.5) from trail_splits ts2) )

        union

        select
            'trail - split' as src,
            geom
        from trail_splits
    """
    db.make_geotable_from_query(
        trail_merge, "trail_merged", geom_type="LINESTRING", epsg=26918
    )


def add_segmentation_to_sidewalks(db: PostgreSQL):

    # Split the sidewalks wherever they intersect a trail
    # ---------------------------------------------------

    sidewalk_split = """
        select
            globalid,
            (st_dump(
                st_split(
                    s.geom,
                    (select st_collect(geom)
                     from ped_trails t
                     where st_intersects(s.geom, t.geom)
                    )
                )
            )).geom
        from pedestriannetwork_lines s
    """
    db.make_geotable_from_query(
        sidewalk_split, "sidewalk_splits", geom_type="LINESTRING", epsg=26918
    )

    # Merge the split sidewalks with any sidewalks that didn't get split
    # ------------------------------------------------------------------

    sidewalk_merge = """
        select
            'sidewalk - raw' as src,
            geom
        from pedestriannetwork_lines
        where
            not st_within(geom, (select st_buffer(st_collect(geom), 0.5) from sidewalk_splits) )

        union

        select
            'sidewalk - split' as src,
            geom
        from sidewalk_splits
    """
    db.make_geotable_from_query(
        sidewalk_merge, "sidewalk_merged", geom_type="LINESTRING", epsg=26918
    )


def merge_sidewalks_and_trails(db: PostgreSQL):
    query = """
        SELECT src, geom FROM trail_merged
        UNION
        SELECT src, geom FROM sidewalk_merged
    """
    db.make_geotable_from_query(
        query, "sidewalks_and_trails", geom_type="LINESTRING", epsg=26918
    )


def cleanup_temp_tables(db: PostgreSQL):
    """ Delete the intermediate tables to keep the DB clean """
    for tbl in ["trail_splits", "trail_merged", "sidewalk_splits", "sidewalk_merged"]:
        db.table_delete(tbl)


def merge_topologies(db: PostgreSQL):
    add_segmentation_to_trails(db)
    add_segmentation_to_sidewalks(db)
    merge_sidewalks_and_trails(db)
    cleanup_temp_tables(db)


if __name__ == "__main__":
    from sidewalk_gaps import CREDENTIALS, PROJECT_DB_NAME

    db = PostgreSQL(PROJECT_DB_NAME, verbosity="minimal", **CREDENTIALS["localhost"])

    merge_topologies(db)

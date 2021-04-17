from postgis_helpers import PostgreSQL


def scrub_osm_tags(db: PostgreSQL, custom_hierarchy: list = None):
    """
    Some streets have multiple OSM 'highway' tags.

    Like this: '{trunk,motorway}'
           or: '{residential,trunk_link}'

    We're using the 'worst' attribute, and
    the hierarchy list is ordered from 'worst'
    to 'best'. It can be overridden with a custom
    hierarchy.
    """

    if custom_hierarchy:
        hierarchy = custom_hierarchy

    else:
        hierarchy = [
            "motorway",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "unclassified",
            "road",
            "bus_guideway",
            "residential",
            "living_street",
            "crossing",
            "service",
            "unsurfaced",
            "escape",
        ]

    query = """
        select distinct highway
        from data_viz.osm_sw_coverage
    """

    tag_list = db.query_as_list(query)

    results = []

    for tag_tuple in tag_list:
        all_tags = tag_tuple[0]

        # Split up any comma-delimited tags
        if "," in all_tags:
            all_tags = all_tags.replace("{", "").replace("}", "").split(",")
        else:
            all_tags = [all_tags]

        lowest_index_number = 999

        for tag in all_tags:

            # Wipe out the "_link" bit
            tag = tag.replace("_link", "")

            # Get the index of this tag within the pre-defined list
            tag_idx = hierarchy.index(tag)

            # Use this tag if it's the lowest index found
            if tag_idx < lowest_index_number:
                lowest_index_number = tag_idx

        results.append((tag_tuple[0], hierarchy[lowest_index_number]))

    db.table_add_or_nullify_column("osm_sw_coverage", "hwy_tag", "TEXT", schema="data_viz")

    for original_tag, simple_tag in results:

        print(f"Updating {original_tag} as {simple_tag}")

        update_query = f"""
            UPDATE data_viz.osm_sw_coverage
            SET hwy_tag = '{simple_tag}'
            WHERE highway = '{original_tag}';
        """
        db.execute(update_query)

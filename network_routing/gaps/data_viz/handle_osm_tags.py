from pg_data_etl import Database


def scrub_osm_tags(db: Database, custom_hierarchy: list = None) -> None:
    """
    - Some streets have multiple OSM 'highway' tags, like `'{trunk,motorway}'` or `'{residential,trunk_link}'`

    - This function finds the 'worst' attribute, following the pre-defined `hierarchy`,
    which is ordered from 'worst' to 'best'. It can be overridden by providing a `custom_hierarchy`.


    Args:
        db (PostgreSQL): analysis database
        custom_hierarchy (list): custom list of OSM tag hierarchy, ordered worst to best.

    Returns:
        Updates `public.osm_edges_drive` in-place
    """

    edge_table = "osm_edges_drive"

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
            "corridor",
            "bus_guideway",
            "residential",
            "living_street",
            "crossing",
            "service",
            "unsurfaced",
            "escape",
        ]

    query = f"""
        select distinct highway
        from public.{edge_table}
        where analyze_sw = 1
    """

    tag_list = db.query_as_list_of_lists(query)

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

    db.execute(
        f"""
        ALTER TABLE {edge_table}
        ADD COLUMN hwy_tag TEXT;
    """
    )

    for original_tag, simple_tag in results:

        print(f"Updating {original_tag} as {simple_tag}")

        update_query = f"""
            UPDATE {edge_table}
            SET hwy_tag = '{simple_tag}'
            WHERE highway = '{original_tag}';
        """
        db.execute(update_query)

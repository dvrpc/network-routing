from helpers import db_connection

db = db_connection()

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
    "escape"
]

query = """
    select distinct highway
    from data_viz.osm_sw_coverage
"""

tag_list = db.query_as_list(query)


results = []

for tag_tuple in tag_list:
    all_tags = tag_tuple[0]

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

        if tag_idx < lowest_index_number:
            lowest_index_number = tag_idx

    results.append((tag_tuple[0], hierarchy[lowest_index_number]))

db.table_add_or_nullify_column("osm_sw_coverage", "osm_hwy_clean", "TEXT", schema="data_viz")

for original_tag, simple_tag in results:
    update_query = f"""
        UPDATE data_viz.osm_sw_coverage
        SET osm_hwy_clean = '{simple_tag}'
        WHERE highway = '{original_tag}';
    """
    db.execute(update_query)
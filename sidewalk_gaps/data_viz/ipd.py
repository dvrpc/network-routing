from helpers import db_connection
from tqdm import tqdm

db = db_connection()


# # Force ipd into 26918
# db.table_reproject_spatial_data("ipd_2018", 4326, 26918, "MULTIPOLYGON")


ipd_tracts = db.query_as_geo_df("SELECT * FROM ipd_2018")


ipd_tracts["sw_len"] = 0.0
ipd_tracts["osm_len"] = 0.0

for idx, row in tqdm(ipd_tracts.iterrows(), total=len(ipd_tracts)):

    for col_name, src_tablename in [
        ("sw_len", "pedestriannetwork_lines"),
        ("osm_len", "osm_edges_drive"),
    ]:
        query = f"""
            select
                sum(
                    st_length(
                        st_intersection(i.geom, t.geom)
                    )
                )
            from
                ipd_2018 i,
                {src_tablename} t
            where
                geoid = '{row.geoid}'
              and
                st_intersects(i.geom, t.geom)
        """

        result = db.query_as_single_item(query)

        ipd_tracts.at[idx, col_name] = result

ipd_tracts["sw_coverage"] = ipd_tracts["sw_len"] / ipd_tracts["osm_len"]

db.import_geodataframe(ipd_tracts, "ipd", schema="data_viz")

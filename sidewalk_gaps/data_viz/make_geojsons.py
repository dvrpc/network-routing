# from tqdm import tqdm

# from postgis_helpers import PostgreSQL
# from sidewalk_gaps import CREDENTIALS

# database_name = "sidewalk_gaps"


# if __name__ == "__main__":
#     db = PostgreSQL(
#         database_name,
#         verbosity="minimal",
#         **CREDENTIALS["localhost"]
#     )

#     tbl = "nj_centerline"

#     query = f"""
#         SELECT sidewalk_3 / st_length(geom) / 2 AS sw_coverage, geom,
#         case when sidewalk_3 / st_length(geom) / 2 = 0 then '#e74c3c'
#         when sidewalk_3 / st_length(geom) / 2 > 0 and sidewalk_3 / st_length(geom) / 2 < 0.4 then '#f5b041'
#         when sidewalk_3 / st_length(geom) / 2 >= 0.4 and sidewalk_3 / st_length(geom) / 2 < 0.8 then '#f7dc6f'
#         else '#52be80' end as color
#         FROM nj_centerline
#     """

#     df = db.query_as_geo_df(query)

#     df.to_file("data_viz/data/sidewalk_classification.json", driver="GeoJSON")
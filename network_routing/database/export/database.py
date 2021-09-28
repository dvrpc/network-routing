import pg_data_etl as pg

from network_routing import (
    pg_db_connection,
    FOLDER_DATA_PRODUCTS,
)


def create_db_for_api():
    """
    Create a new database for the Sidewalk Priorities API,
    and save it to .sql file using pg_dump
    """

    source_db = pg_db_connection()

    new_db = pg.Database.from_config(
        "sidewalk_priorities_api",
        "localhost",
        bin_paths={"psql": "/Applications/Postgres.app/Contents/Versions/latest/bin"},
    )

    new_db.admin("DROP")
    new_db.admin("CREATE")

    queries = {
        "api.isochrones": """
            select * from data_viz.isochrones_mcpc_combined_pois
        """,
        "api.missing_links": """
            select * from improvements.montgomery_split
        """,
        "api.montco_munis": """
            select mun_name, geom from municipalboundaries m 
            where co_name = 'Montgomery' and state_name = 'Pennsylvania'
        """,
        "api.pois": """
            with centroids as (
                    select
                        poi_name,
                        category,
                        poi_uid,
                        ab_ratio,
                        st_centroid(st_collect(geom)) as geom
                    from
                        data_viz.ab_ratio_mcpc_combined_pois
                    where category != 'NJT rail'
                    group by
                        poi_name, category, poi_uid, ab_ratio
            )
            select
                st_collect(geom) as geom, 
                poi_name, 
                category, 
                min(poi_uid) as poi_uid, 
                ab_ratio
            from
                centroids
            group by
                poi_name, category, ab_ratio, geom
        """,
    }

    # Import each table to the new database
    for new_tablename, query in queries.items():
        gdf = source_db.gdf(query)

        print(f"Importing {new_tablename}")

        new_db.import_geodataframe(gdf, new_tablename)

    # Write the resulting database to .sql dump file
    new_db.dump(FOLDER_DATA_PRODUCTS)


if __name__ == "__main__":
    create_db_for_api()

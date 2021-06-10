import pandas as pd
from tqdm import tqdm
import sqlalchemy
from geoalchemy2 import Geometry, WKTElement
from pg_data_etl import Database

from network_routing import pg_db_connection

# This silences the geopandas warning: "UserWarning: Geometry column does not contain geometry."
import warnings

warnings.filterwarnings("ignore")


def erase_features(db: Database, tablename: str = "data_viz.all_possible_improvements") -> None:
    """
    Iterate over all features in the 'all_possible_improvements' table.

    Erase any parts of the geometry within a 10 meter buffer of nearby sidewalks.
    Keep whatever remains and write to a new table named: 'data_viz.cleaned_improvements'
    """

    uids = db.query_as_list_of_singletons(
        f"""
        select uid from {tablename}
    """
    )

    gdfs = []

    # Iterate over every feature that was previously drawn

    for uid in tqdm(uids, total=len(uids)):

        q = f"""
        with seg as (
            -- filter new segments to a single new geometry
            
            select geom 
            from {tablename} 
            where uid = {uid}
        ),
        sw_buff as (
            -- select sidewalks within 10meters
            -- and turn those features into a single buffer poly

            select st_buffer(st_collect(pl.geom), 10) as geom
            from pedestriannetwork_lines pl, seg
            where st_dwithin(pl.geom, seg.geom, 10)
        ),
        diff as (
            -- find the line geometry that does not intersect the poly
            
            select st_difference(s.geom, b.geom) as geom
            from seg s, sw_buff b
        )
        select geom
        from diff
        """

        gdf = db.gdf(q)

        if gdf.iloc[0].geom is None:
            # a None result means there is zero overlap and we want to grab the whole source feature

            gdf = db.gdf(
                f"""
                select geom from {tablename} where uid = {uid}
            """
            )

            gdf["src_uid"] = uid

            gdfs.append(gdf)

        elif gdf.iloc[0].geom.is_empty:
            # An empty result means the entire source geometry was erased (i.e. this sw already exists fully)
            pass
        else:
            # Something remained after the erase, so let's keep what we got

            gdf["src_uid"] = uid
            gdfs.append(gdf)

    # Write a single table with all of the results to PostGIS

    db.import_geodataframe(
        pd.concat(gdfs),
        "data_viz.cleaned_improvements",
        explode=True,
        gpd_kwargs={"if_exists": "append"},
    )


if __name__ == "__main__":
    db = pg_db_connection()
    erase_features(db)
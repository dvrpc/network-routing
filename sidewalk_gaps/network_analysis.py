from sqlalchemy import create_engine
from postgis_helpers import PostgreSQL
import pandana as pdna
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from geoalchemy2 import Geometry, WKTElement

WALKING_SPEED_MPH = 2.5


class SidewalkNetwork:

    def __init__(self,
                 db: PostgreSQL,
                 schema: str,
                 walking_mph: float = 2.5,
                 max_minutes: float = 60.0):

        self.db = db
        self.schema = schema
        self.walking_mph = walking_mph
        self.max_minutes = max_minutes
        self.themes = self.get_themes()

    def get_themes(self):
        theme_query = f"""
            SELECT distinct theme
            FROM {self.schema}.points_of_interest
        """
        themes = self.db.query_as_list(theme_query)
        themes = {x[0]: x[0] for x in themes}

        for theme in themes:
            nice_theme = theme.lower().replace(" ", "").replace("/", "")
            themes[theme] = nice_theme

        return themes

    def _prep_raw_geom_table(self,
                             table_name: str,
                             geom_type: str,
                             epsg: int = 26918,
                             id_col: str = "uid"):
        
        uid_query = f"""
            ALTER TABLE {self.schema}.{table_name} ADD {id_col} serial PRIMARY KEY;
        """

        index_query = f"""
            CREATE INDEX ON {self.schema}.{table_name} USING GIST (geom);
        """

        update_geom_table = f"""
            ALTER TABLE {self.schema}.{table_name}
            ALTER COLUMN geom TYPE geometry({geom_type}, {epsg})
            USING ST_Transform(ST_SetSRID(geom, {epsg}), {epsg});
        """

        for query in [uid_query, index_query, update_geom_table]:
            self.db.execute(query)

    def _make_geotable_from_query(self, query, **kwargs):
        self.db.execute(query)
        self._prep_raw_geom_table(**kwargs)

    # Set up the analysis by: 
    # 1) making nodes
    # 2) assigning node ids to the edge network
    # 3) adding travel time weights (walking)

    def setup(self):
        self.make_nodes()
        self.assign_node_ids_to_network()
        self.add_travel_time_weights()

    def make_nodes(self):

        query = f"""
            DROP TABLE IF EXISTS {self.schema}.nodes;
            CREATE TABLE {self.schema}.nodes AS
            SELECT st_startpoint(geom) AS geom
            FROM {self.schema}.pedestriannetwork_lines
            UNION
            SELECT st_endpoint(geom) AS geom
            FROM {self.schema}.pedestriannetwork_lines
            GROUP BY geom
        """

        self._make_geotable_from_query(query,
                                       table_name="nodes",
                                       geom_type="Point",
                                       id_col="node_id")

    def assign_node_ids_to_network(self):

        for column_name in ["start_id", "end_id"]:
            query = f"""
                ALTER TABLE {self.schema}.pedestriannetwork_lines
                ADD COLUMN {column_name} INT;
            """
            self.db.execute(query)

        start_id_query = f"""
            UPDATE {self.schema}.pedestriannetwork_lines ln
            SET start_id = (SELECT pt.node_id
                            FROM {self.schema}.nodes pt
                            WHERE ST_DWITHIN(pt.geom, st_startpoint(ln.geom), 5)
                            ORDER BY ST_DISTANCE(pt.geom,
                                                st_startpoint(ln.geom))
                                    ASC LIMIT 1)
        """

        self.db.execute(start_id_query)

        end_id_query = start_id_query.replace("start", "end")

        self.db.execute(end_id_query)

    def add_travel_time_weights(self):

        # Add a meter length and minutes column
        for column_name in ["len_meters", "minutes"]:
            query = f"""
                ALTER TABLE {self.schema}.pedestriannetwork_lines
                ADD COLUMN {column_name} FLOAT;
            """
            self.db.execute(query)

        # Capture length in meters into its own column
        update_meters = f"""
            UPDATE {self.schema}.pedestriannetwork_lines
            SET len_meters = ST_LENGTH(geom);
        """
        self.db.execute(update_meters)

        # Calculate walking travel time in minutes
        update_minutes = f"""
            UPDATE {self.schema}.pedestriannetwork_lines
            SET minutes = len_meters / 1609.34 / {self.walking_mph} * 60;
        """
        self.db.execute(update_minutes)

    # Build the network with Pandana

    def construct_network(self):

        # EDGES
        query = f"SELECT * FROM {self.schema}.pedestriannetwork_lines"
        edge_gdf = self.db.query_as_geo_df(query)

        # NODES
        node_query = f"""
            SELECT node_id,
                ST_X(st_transform(geom, 4326)) as x,
                ST_Y(st_transform(geom, 4326)) as y,
                geom
            FROM {self.schema}.nodes
        """
        node_gdf = self.db.query_as_geo_df(node_query)

        # Force the ID columns in the EDGE gdf to integer
        for col in ["start_id", "end_id"]:
            edge_gdf[col] = edge_gdf[col].astype(int)

        # Set the index of the NODE gdf to the uid column
        node_gdf.set_index('node_id', inplace=True)

        # Build the pandana network
        network = pdna.Network(
            node_gdf["x"], node_gdf["y"],
            edge_gdf["start_id"], edge_gdf["end_id"], edge_gdf[["minutes"]],
            twoway=True
        )

        network.precompute(self.max_minutes)

        # Save the network and geodataframes within the object
        self.network = network
        self.edge_gdf = edge_gdf
        self.node_gdf = node_gdf

    # Add and analyze access to points of interest
    # --------------------------------------------

    def add_pois_to_network(self):
        for theme in self.themes:
            poi_gdf, _ = self.calculate_single_poi(theme)
            self.qaqc_poi_assignment(theme, poi_gdf)

    def qaqc_poi_assignment(self, theme: str, poi_gdf: gpd.GeoDataFrame):

        # Save the network assignment for QAQC
        poi_gdf["node_id"] = self.network.get_node_ids(poi_gdf["x"],
                                                       poi_gdf["y"],
                                                       mapping_distance=1)
        poi_node_pairs = pd.merge(poi_gdf,
                                  self.node_gdf,
                                  left_on='node_id',
                                  right_on='node_id',
                                  how='left',
                                  sort=False,
                                  suffixes=['_from', '_to'])

        poi_node_pairs["flow"] = [
            LineString([row["geom_from"], row["geom_to"]]) for idx, row in poi_node_pairs.iterrows()
        ]
        poi_node_pairs = poi_node_pairs.set_geometry("flow")

        poi_node_pairs['geom'] = poi_node_pairs["flow"].apply(
                                    lambda x: WKTElement(x.wkt, srid=26918)
        )

        for col in ["flow", "geom_from", "geom_to"]:
            poi_node_pairs.drop(col, inplace=True, axis=1)

        engine = create_engine(self.db.uri())
        poi_node_pairs.to_sql(f"poi_{self.themes[theme]}_qa",
                              engine,
                              schema=self.schema,
                              dtype={'geom': Geometry("LineString", srid=26918)})
        engine.dispose()

        self.poi_gdf = poi_gdf

    def calculate_single_poi(self, this_theme: str):
        nice_theme = self.themes[this_theme]
        print(nice_theme)

        # POIS
        poi_query = f"""
            SELECT *,
                ST_X(st_transform(geom, 4326)) as x,
                ST_Y(st_transform(geom, 4326)) as y
            FROM {self.schema}.points_of_interest
            WHERE theme = '{this_theme}'
        """
        poi_gdf = self.db.query_as_geo_df(poi_query)

        self.network.set_pois(
            category=nice_theme,
            x_col=poi_gdf["x"],
            y_col=poi_gdf["y"],
            maxdist=self.max_minutes,
            maxitems=5
        )

        result_matrix = self.network.nearest_pois(distance=self.max_minutes,
                                                  category=nice_theme,
                                                  num_pois=5)

        new_colnames = {}
        for column in result_matrix.columns:
            new_name = f'n_{column}'
            new_colnames[column] = new_name

        result_matrix = result_matrix.rename(index=str, columns=new_colnames)

        engine = create_engine(self.db.uri())
        result_matrix.to_sql(
            f"poi_{nice_theme}",
            engine,
            schema=self.schema,
            if_exists="replace"
        )
        engine.dispose()

        self.add_geometries_to_accessibilty_result(f"poi_{nice_theme}")

        return poi_gdf, result_matrix

    def add_geometries_to_accessibilty_result(self, table_name: str):

        add_geom_col = f"""
            SELECT AddGeometryColumn('{self.schema}', '{table_name}', 'geom', 26918, 'POINT', 2);
        """
        self.db.execute(add_geom_col)

        update_geom_col = f"""
            UPDATE {self.schema}.{table_name} t
            SET geom = (select n.geom from {self.schema}.nodes n
                        where n.node_id::int = t.node_id::int)
        """
        self.db.execute(update_geom_col)

        add_primary_key = f"""
            ALTER TABLE {self.schema}.{table_name}
            ADD PRIMARY KEY (node_id);
        """
        self.db.execute(add_primary_key)

    # QAQC!!!
    # -------
    # def qaqc_poi_assignment(self, this_theme: str):

if __name__ == "__main__":
    from sidewalk_gaps import CREDENTIALS

    schema = "nj"

    db = PostgreSQL(
        "sidewalk_gaps",
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )

    network = SidewalkNetwork(db, schema)
    network.setup()
    network.construct_network()
    network.add_pois_to_network()
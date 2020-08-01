from sqlalchemy import create_engine
from postgis_helpers import PostgreSQL
import pandana as pdna
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from geoalchemy2 import Geometry, WKTElement


class SidewalkNetwork:

    def __init__(self,
                 db: PostgreSQL,
                 schema: str,
                 walking_mph: float = 2.5,
                 max_minutes: float = 180.0,
                 epsg: int = 26918,
                 edge_table_name: str = "sidewalks",
                 run_on_create: bool = True):

        # Capture user input
        self.db = db
        self.schema = schema
        self.walking_mph = walking_mph
        self.max_minutes = max_minutes
        self.epsg = epsg
        self.edge_table_name = edge_table_name

        # Get a list of POI themes within the schema
        self.themes = self._get_themes()

        # Set the SQL database schema to the active schema
        self.db.ACTIVE_SCHEMA = schema

        if run_on_create:
            self.setup()
            self.construct_network()
            self.analyze_pois()

    def _get_themes(self):
        """
        Return a dictionary with each unique POI theme within the schema.

        Key is the raw text from SQL, value is the santinized table name

            ```{"Food/Drink": "fooddrink",
                "Library"   : "library",}```

        """
        theme_query = f"""
            SELECT distinct theme
            FROM {self.schema}.points_of_interest
        """
        themes = self.db.query_as_list(theme_query)
        themes = {x[0]: x[0] for x in themes}

        for theme in themes:
            nice_theme = theme.lower().replace(" ", "").replace(r"/", "")
            themes[theme] = nice_theme

        return themes

    # PREPARE THE NETWORK FOR ANALYSIS
    # --------------------------------

    def setup(self):
        """
        Set up the analysis by:
            1) making nodes
            2) assigning node ids to the edge network
            3) adding travel time weights (walking)
        """
        # self.make_nodes()
        self.assign_node_ids_to_network()
        self.add_travel_time_weights()

    # def make_nodes(self):
    #     """
    #     Use the edge table to generate a set of nodes.

    #     These nodes are all of the unique start and
    #     endpoints of the line segments.
    #     """

    #     query = f"""
    #         SELECT st_startpoint(geom) AS geom
    #         FROM {self.schema}.{self.edge_table_name}
    #         UNION
    #         SELECT st_endpoint(geom) AS geom
    #         FROM {self.schema}.{self.edge_table_name}
    #         GROUP BY geom
    #     """

    #     self.db.make_geotable_from_query(query,
    #                                      new_table_name="nodes",
    #                                      geom_type="Point",
    #                                      epsg=self.epsg,
    #                                      uid_col="node_id")

    def assign_node_ids_to_network(self):
        """
        Using the newly-created node table, we now
        need to assign two node_id values to each
        segment: one at the start, one at the end.
        """

        # Add columns for the start and end node_id values
        for column_name in ["start_id", "end_id"]:
            self.db.table_add_or_nullify_column(self.edge_table_name,
                                                column_name, "INT")

        # Execute the query for the START of each segment
        start_id_query = f"""
            UPDATE {self.schema}.{self.edge_table_name} ln
            SET start_id = (SELECT pt.sw_node_id
                            FROM {self.schema}.sw_nodes pt
                            WHERE ST_DWITHIN(pt.geom, st_startpoint(ln.geom), 5)
                            ORDER BY ST_DISTANCE(pt.geom,
                                                st_startpoint(ln.geom))
                                    ASC LIMIT 1)
        """
        self.db.execute(start_id_query)

        # Execute the query for the END of each segment
        end_id_query = start_id_query.replace("start", "end")
        self.db.execute(end_id_query)

    def add_travel_time_weights(self):
        """
        Add impedence columns to the edges.

            1) Calculate the legnth in meters (epsg:26918)
            2) Convert meters into minutes:
                - divide by 1609.34
                - divide by defined walking speed in MPH
                - multiply by 60 to get minutes
        """

        # Add a meter length and minutes column
        for column_name in ["len_meters", "minutes"]:
            self.db.table_add_or_nullify_column(self.edge_table_name,
                                                column_name, "FLOAT")

        # Capture length in meters into its own column
        update_meters = f"""
            UPDATE {self.schema}.{self.edge_table_name}
            SET len_meters = ST_LENGTH(geom);
        """
        self.db.execute(update_meters)

        # Calculate walking travel time in minutes
        update_minutes = f"""
            UPDATE {self.schema}.{self.edge_table_name}
            SET minutes = len_meters / 1609.34 / {self.walking_mph} * 60;
        """
        self.db.execute(update_minutes)

    # TURN THE POSTGIS DATA INTO A PANDANA NETWORK
    # --------------------------------------------

    def construct_network(self):

        # Get all edges
        query = f"SELECT * FROM {self.schema}.{self.edge_table_name}"
        edge_gdf = self.db.query_as_geo_df(query)

        # Get all nodes
        node_query = f"""
            SELECT sw_node_id AS node_id,
                ST_X(st_transform(geom, 4326)) as x,
                ST_Y(st_transform(geom, 4326)) as y,
                geom
            FROM {self.schema}.sw_nodes
        """
        node_gdf = self.db.query_as_geo_df(node_query)

        # Force the ID columns in the edge gdf to integer
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

    # ANALYZE POINTS OF INTEREST
    # --------------------------

    def analyze_pois(self):
        """
        For each theme in the POI table:
            1) Run ``calculate_single_poi()``
            2) Add a QAQC table showing the POI->Node assignment
        """
        all_results = []
        for theme in self.themes:
            poi_gdf, access_results = self.calculate_single_poi(theme)
            self.qaqc_poi_assignment(theme, poi_gdf)

            all_results.append(access_results)

        df_all_access_results = pd.concat(all_results, axis=1, sort=False)

        self.db.import_dataframe(df_all_access_results,
                                 "access_table",
                                 if_exists="replace")

        final_result_query = f"""
            select r.*, n.geom
            from {self.schema}.sw_nodes n
            left join {self.schema}.access_table r
            on n.sw_node_id::int = r.node_id::int
        """
        self.db.make_geotable_from_query(final_result_query, "access_results", "Point", self.epsg)

    def calculate_single_poi(self, this_theme: str):
        """
        1) Add all POIs for a given theme to the network.
        2) Calculate the minutes away for the 5 nearest POIs of this theme.
        3) Save the result to non-spatial SQL table
        4) Run ``add_geometries_to_accessibilty_result()``

        Result
        ------
            New table in DB. Each row is a node, and each column
            has the time to walk to the N-nearest POI.
        """

        nice_theme = self.themes[this_theme]

        # POIS
        poi_query = f"""
            SELECT *,
                ST_X(st_transform(geom, 4326)) as x,
                ST_Y(st_transform(geom, 4326)) as y
            FROM {self.schema}.points_of_interest
            WHERE theme = '{this_theme}'
        """
        poi_gdf = self.db.query_as_geo_df(poi_query)

        # TODO: find a way to enforce max matching distance
        self.network.set_pois(
            category=nice_theme,
            x_col=poi_gdf["x"],
            y_col=poi_gdf["y"],
            maxdist=self.max_minutes,
            maxitems=3
        )

        result_matrix = self.network.nearest_pois(distance=self.max_minutes,
                                                  category=nice_theme,
                                                  num_pois=3)

        new_colnames = {}
        for column in result_matrix.columns:
            new_name = f'n_{column}_{this_theme}'
            new_colnames[column] = new_name

        result_matrix = result_matrix.rename(index=str, columns=new_colnames)

        # self.db.import_dataframe(result_matrix, f"poi_{nice_theme}", if_exists="replace")
        # self.add_geometries_to_accessibilty_result(f"poi_{nice_theme}")

        return poi_gdf, result_matrix

    # def add_geometries_to_accessibilty_result(self, table_name: str):
    #     """
    #     Spatialize the non-spatial POI result table with node geometries
    #     """

    #     add_geom_col = f"""
    #         SELECT AddGeometryColumn(
    #             '{self.schema}',
    #             '{table_name}',
    #             'geom',
    #             {self.epsg},
    #             'POINT',
    #             2
    #         );
    #     """
    #     self.db.execute(add_geom_col)

    #     update_geom_col = f"""
    #         UPDATE {self.schema}.{table_name} t
    #         SET geom = (select n.geom from {self.schema}.nodes n
    #                     where n.node_id::int = t.node_id::int)
    #     """
    #     self.db.execute(update_geom_col)

    #     # Register node_id as the primary key for the table
    #     add_primary_key = f"""
    #         ALTER TABLE {self.schema}.{table_name}
    #         ADD PRIMARY KEY (node_id);
    #     """
    #     self.db.execute(add_primary_key)

    def qaqc_poi_assignment(self, theme: str, poi_gdf: gpd.GeoDataFrame):
        """
        For a given poi geodataframe:
            1) Get the ID of the nearest node for each POI
            2) Add a 'flow' geometry from the POI to the assigned node
            3) Delete all other geometries in the table and write to SQL
        """

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
                                    lambda x: WKTElement(x.wkt, srid=self.epsg)
        )

        for col in ["flow", "geom_from", "geom_to"]:
            poi_node_pairs.drop(col, inplace=True, axis=1)

        engine = create_engine(self.db.uri())
        poi_node_pairs.to_sql(f"poi_{self.themes[theme]}_qa",
                              engine,
                              schema=self.schema,
                              if_exists="replace",
                              dtype={'geom': Geometry("LineString", srid=self.epsg)})
        engine.dispose()

        self.poi_gdf = poi_gdf


if __name__ == "__main__":
    from sidewalk_gaps import CREDENTIALS

    schema = "camden"

    db = PostgreSQL(
        "sidewalk_gaps",
        verbosity="minimal",
        **CREDENTIALS["localhost"]
    )

    network = SidewalkNetwork(db, schema)

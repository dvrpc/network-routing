from sqlalchemy import create_engine
from postgis_helpers import PostgreSQL
import pandana as pdna
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from geoalchemy2 import Geometry, WKTElement


class RoutableNetwork:
    """
    Build a routable network using `pandana` and analyze network-based
    distance to the N-nearest POI(s) by group.

    This requires three input tables:

    1. Edges: linear features with valid topology
    2. Nodes: point features, one for each topological connection
    3. Points of Interest (POIs): point features showing locations to route people from. Must have an ID column to distinguish between the points.

    Attributes:
        db (PostgreSQL): database, the same thing returned from `network_routing.db_connection()`
        schema (str): name of the schema where the analysis data can be found
        edge_table_name (str): name of the sidewalk, OSM, or other edge layer being analyzed
        node_table_name (str): name of nodes that correspond to the edge table
        node_id_column (str): name of unique ID column in the node table
        poi_table_name (str): name of POI table to analyze
        poi_id_column (str): name of ID column in the POI table, can be one or many features per ID. More than one feature for a given ID will get treated as a group.
        output_table_name (str): base tablename for results of analysis (network node geometry + accessibility attribute columns)
        output_schema (str): schema to store output analysis result + QAQC layers
        walking_mph (float): assumed pedestrian walking speed in miles-per-hour, defaults to `2.5`
        max_minutes (float): distance(/time) threshold to the analysis, defaults to `45`
        epsg (int): spatial data projection, defaults to `26918`
        num_pois (int): number of POIs to analyze when provided with groups (i.e. multiple features per ID), defaults to `3`
        poi_match_threshold (int): maximum allowable snapping distance between POI and node layers, defaults to `45`
        run_on_create (bool): flag that controls whether or not the analysis is run when the analysis object is instantiated from the class, defaults to `True`


    Returns:
        RoutableNetwork: network model
    """

    def __init__(
        self,
        db: PostgreSQL,
        schema: str,
        edge_table_name: str,
        node_table_name: str,
        node_id_column: str,
        poi_table_name: str,
        poi_id_column: str,
        output_table_name: str,
        output_schema: str,
        walking_mph: float = 2.5,
        max_minutes: float = 45,
        epsg: int = 26918,
        num_pois: int = 3,
        poi_match_threshold: int = 45,
        run_on_create: bool = True,
    ):

        # Capture user input
        self.db = db
        self.schema = schema
        self.walking_mph = walking_mph
        self.max_minutes = max_minutes
        self.epsg = epsg
        self.edge_table_name = edge_table_name
        self.node_table_name = node_table_name
        self.node_id_column = node_id_column
        self.poi_table_name = poi_table_name
        self.poi_id_column = poi_id_column
        self.output_table_name = output_table_name
        self.output_schema = output_schema
        self.num_pois = num_pois
        self.poi_match_threshold = poi_match_threshold

        # Get a list of POI themes within the schema
        self.themes = self._get_themes()

        # Set the SQL database schema to the active schema
        self.db.ACTIVE_SCHEMA = schema

        # Placeholders for network and geodataframes
        self.network = None
        self.edge_gdf = None
        self.node_gdf = None
        self.poi_gdf = None

        if run_on_create:

            self._setup()
            self._construct_network()
            self._analyze_pois()

    def _get_themes(self):
        """
        Return a dictionary with each unique POI 'theme' within the schema.

        In this case, a 'theme' is any kind of unique identifier.

        Key is the raw text from SQL, value is the santinized table name

            {"Food/Drink": "fooddrink",
             "Library"   : "library",}

        """
        theme_query = f"""
            SELECT distinct {self.poi_id_column}::text
            FROM {self.schema}.{self.poi_table_name}
        """
        themes = self.db.query_as_list(theme_query)
        themes = {x[0]: x[0] for x in themes}

        bad_characters = [" ", r"/", "-"]

        for theme in themes:

            nice_theme = theme.lower()

            for char in bad_characters:
                nice_theme = nice_theme.replace(char, "")

            themes[theme] = nice_theme

        return themes

    # PREPARE THE NETWORK FOR ANALYSIS
    # --------------------------------

    def _setup(self):
        """
        Set up the analysis by:
            1) assigning node ids to the edge network
            2) adding travel time weights (walking)

        Only execute these functions if they haven't been done yet
        """

        edge_columns = self.db.table_columns_as_list(
            table_name=self.edge_table_name, schema=self.schema
        )

        if "start_id" not in edge_columns:
            self._assign_node_ids_to_network()

        if "minutes" not in edge_columns:
            self._add_travel_time_weights()

    def _assign_node_ids_to_network(self):
        """
        Using the newly-created node table, we now
        need to assign two node_id values to each
        segment: one at the start, one at the end.
        """

        print("Assigning Node ID values to the edge table")

        # Add columns for the start and end node_id values
        for column_name in ["start_id", "end_id"]:
            self.db.table_add_or_nullify_column(self.edge_table_name, column_name, "INT")

        # Execute the query for the START of each segment
        start_id_query = f"""
            UPDATE {self.schema}.{self.edge_table_name} ln
            SET start_id = (SELECT pt.{self.node_id_column}
                            FROM {self.schema}.{self.node_table_name} pt
                            WHERE ST_DWITHIN(pt.geom, st_startpoint(ln.geom), 5)
                            ORDER BY ST_DISTANCE(pt.geom,
                                                st_startpoint(ln.geom))
                                    ASC LIMIT 1)
        """
        self.db.execute(start_id_query)

        # Execute the query for the END of each segment
        end_id_query = start_id_query.replace("start", "end")
        self.db.execute(end_id_query)

    def _add_travel_time_weights(self):
        """
        Add impedence columns to the edges.

            1) Calculate the legnth in meters (epsg:26918)
            2) Convert meters into minutes:
                - divide by 1609.34
                - divide by defined walking speed in MPH
                - multiply by 60 to get minutes
        """

        print("Adding travel time weights to the edge table")

        # Add a meter length and minutes column
        for column_name in ["len_meters", "minutes"]:
            self.db.table_add_or_nullify_column(self.edge_table_name, column_name, "FLOAT")

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

    def _construct_network(self):

        # Get all edges
        query = f"""
            SELECT start_id, end_id, minutes, geom
            FROM {self.schema}.{self.edge_table_name}
            WHERE start_id IN (
                    select distinct {self.node_id_column}
                    FROM {self.schema}.{self.node_table_name}
                )
                AND
                end_id IN (
                    select distinct {self.node_id_column}
                    FROM {self.schema}.{self.node_table_name}
                )
        """
        edge_gdf = self.db.query_as_geo_df(query)

        # Get all nodes
        node_query = f"""
            SELECT {self.node_id_column} AS node_id,
                ST_X(st_transform(geom, 4326)) as x,
                ST_Y(st_transform(geom, 4326)) as y,
                geom
            FROM {self.schema}.{self.node_table_name}
        """
        node_gdf = self.db.query_as_geo_df(node_query)

        # Force the ID columns in the edge gdf to integer
        for col in ["start_id", "end_id"]:
            edge_gdf[col] = edge_gdf[col].astype(int)

        # Set the index of the NODE gdf to the uid column
        node_gdf.set_index("node_id", inplace=True)

        print(node_gdf.dtypes)
        print(edge_gdf.dtypes)

        # Build the pandana network
        print("Making network")
        network = pdna.Network(
            node_gdf["x"],
            node_gdf["y"],
            edge_gdf["start_id"],
            edge_gdf["end_id"],
            edge_gdf[["minutes"]],
            twoway=True,
        )
        print("Precomputing the network")
        network.precompute(self.max_minutes)

        # Save the network and geodataframes within the object
        self.network = network
        self.edge_gdf = edge_gdf
        self.node_gdf = node_gdf

    # ANALYZE POINTS OF INTEREST (/transit stops!)
    # --------------------------------------------

    def _analyze_pois(self):
        """
        For each theme in the POI table:
            1) Run ``calculate_single_poi()``
            2) Add a QAQC table showing the POI->Node assignment
        """
        all_results = []
        for theme in self.themes:
            print("\t->", theme)
            poi_gdf, access_results = self._calculate_single_poi(theme)

            if access_results is not None:
                self._qaqc_poi_assignment(theme, poi_gdf)
                all_results.append(access_results)

        df_all_access_results = pd.concat(all_results, axis=1, sort=False)

        self.db.import_dataframe(
            df_all_access_results,
            f"{self.output_table_name}_table",
            if_exists="replace",
        )

        final_result_query = f"""
            select r.*, n.geom
            from {self.schema}.{self.node_table_name} n
            left join {self.schema}.{self.output_table_name}_table r
            on n.{self.node_id_column}::int = r.node_id::int
        """
        self.db.make_geotable_from_query(
            final_result_query, f"{self.output_table_name}_results", "Point", self.epsg
        )

        # Move results into a new schema and merge all QA tables into one
        tables_to_move = [
            f"{self.output_table_name}_table",
            f"{self.output_table_name}_results",
        ]
        self._cleanup_outputs(tables_to_move)

    def _calculate_single_poi(self, this_theme: str):
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

        # Get all POIs by theme
        # that are within 45 meters of a sidewalk (aka 150 feet)
        poi_query = f"""
            SELECT *,
                ST_X(st_transform(geom, 4326)) as x,
                ST_Y(st_transform(geom, 4326)) as y
            FROM {self.schema}.{self.poi_table_name}
            WHERE {self.poi_id_column} = '{this_theme}'
            AND ST_DWITHIN(
                geom,
                (SELECT ST_COLLECT(geom) FROM {self.schema}.{self.edge_table_name}),
                {self.poi_match_threshold}
            )
        """
        poi_gdf = self.db.query_as_geo_df(poi_query)

        # If there aren't any rows in the query result,
        # there are no POIs of this theme that are 'close enough'
        # to the sidewalk network.
        # Break out of function early if this happens.
        if poi_gdf.shape[0] == 0:
            return None, None

        self.network.set_pois(
            category=nice_theme,
            x_col=poi_gdf["x"],
            y_col=poi_gdf["y"],
            maxdist=self.max_minutes,
            maxitems=self.num_pois,
        )

        result_matrix = self.network.nearest_pois(
            distance=self.max_minutes, category=nice_theme, num_pois=self.num_pois
        )

        # # Make sure 'food/drink' turns into 'food_drink'
        # theme_name_for_postgres = this_theme.replace(r"/", "_")

        new_colnames = {}
        for column in result_matrix.columns:
            new_name = f"n_{column}_{nice_theme}"
            new_colnames[column] = new_name

        result_matrix = result_matrix.rename(index=str, columns=new_colnames)

        return poi_gdf, result_matrix

    def _qaqc_poi_assignment(self, theme: str, poi_gdf: gpd.GeoDataFrame):
        """
        For a given poi geodataframe:
            1) Get the ID of the nearest node for each POI
            2) Add a 'flow' geometry from the POI to the assigned node
            3) Delete all other geometries in the table and write to SQL
        """

        # Save the network assignment for QAQC
        poi_gdf["node_id"] = self.network.get_node_ids(
            poi_gdf["x"], poi_gdf["y"], mapping_distance=1
        )
        poi_node_pairs = pd.merge(
            poi_gdf,
            self.node_gdf,
            left_on="node_id",
            right_on="node_id",
            how="left",
            sort=False,
            suffixes=["_from", "_to"],
        )

        poi_node_pairs["flow"] = [
            LineString([row["geom_from"], row["geom_to"]]) for idx, row in poi_node_pairs.iterrows()
        ]
        poi_node_pairs = poi_node_pairs.set_geometry("flow")

        poi_node_pairs["geom"] = poi_node_pairs["flow"].apply(
            lambda x: WKTElement(x.wkt, srid=self.epsg)
        )

        for col in ["flow", "geom_from", "geom_to"]:
            poi_node_pairs.drop(col, inplace=True, axis=1)

        engine = create_engine(self.db.uri())
        poi_node_pairs.to_sql(
            f"poi_{self.themes[theme]}_qa",
            engine,
            schema=self.schema,
            if_exists="replace",
            dtype={"geom": Geometry("LineString", srid=self.epsg)},
        )
        engine.dispose()

        self.poi_gdf = poi_gdf

    def _cleanup_outputs(
        self,
        tables_to_move: list,
    ):
        """ Move results to new schema and merge all tables prefixed with 'poi_' """

        schema_query = f"""
            DROP SCHEMA IF EXISTS {self.output_schema} CASCADE;
            CREATE SCHEMA {self.output_schema};
        """

        self.db.execute(schema_query)

        for table in tables_to_move:
            move_schema_query = f"""
                ALTER TABLE {self.schema}.{table}
                SET SCHEMA {self.output_schema};
            """
            self.db.execute(move_schema_query)

        qa_tables = [x for x in self.db.all_spatial_tables_as_dict() if x[:4] == "poi_"]

        if len(qa_tables) >= 2:

            qa_subqueries = [
                f"SELECT {self.poi_id_column}, geom FROM {self.schema}.{x}" for x in qa_tables
            ]

            query = """
                UNION
            """.join(
                qa_subqueries
            )

            self.db.make_geotable_from_query(
                query, "qaqc_node_match", "LINESTRING", 26918, schema=self.output_schema
            )

        for qa_table in qa_tables:
            self.db.table_delete(qa_table, schema=self.output_schema)

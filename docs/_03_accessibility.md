# Accessibility

The core logic for the accessibility analysis is encapsulated within the [`RoutableNetwork`](https://github.com/dvrpc/network-routing/blob/master/network_routing/accessibility/routable_network.py#L10) class.

## Python usage

To use directly in a Python process, import the `RoutableNetwork` class from the `network_routing` module and instantiate the class with keyword arguments

```python
>>> from network_routing import RoutableNetwork, db_connection
>>> db = db_connection()
>>> my_kwargs = {"poi_table_name": "my_table_name", "poi_id_column": "id_colname"}
>>> net = RoutableNetwork(db, "schema_name", **my_kwargs)
```

## CLI usage

A command-line-interface is provided under the top-level name `access`.

To execute the default analysis, run:

```bash
> access sw-default
```

There are a number of configurations, all of which can be found within [`network_routing/accessibility/cli.py`](https://github.com/dvrpc/network-routing/blob/master/network_routing/accessibility/cli.py).

You can also see a list of all available configurations by running `access --help`

```bash
> access --help

Usage: access [OPTIONS] COMMAND [ARGS]...

  The command 'access' is used to run an accessibility analysis against
  point-of-interest + network edge datasets

Options:
  --help  Show this message and exit.

Commands:
  osm-ridescore  Analyze OSM network distance around each rail stop
  sw-default     Run the RoutableNetwork with default settings
  sw-ridescore   Analyze sidewalk network distance around each rail stop
```

## Analysis parameters

### Required Arguments

`RoutableNetwork()` takes two required positional arguments:

#### Database / schema

- `db: PostgreSQL` == this is the same thing returned from `network_routing.db_connection()`
- `schema: str` == name of the schema where the analysis data can be found

It also requires the following keyword arguments:

#### Edges

- `edge_table_name: str` == name of the sidewalk, OSM, or other edge layer being analyzed

#### Nodes

- `node_table_name: str` == name of nodes that correspond to the edge table
- `node_id_column: str` == name of unique ID column in the node table

#### Points-of-Interest (POI)

- `poi_table_name: str` == name of POI table to analyze
- `poi_id_column: str` == name of ID column in the POI table, can be one or many features per ID. More than one feature for a given ID will get treated as a group.

#### Output schema/tablename(s)

- `output_table_name: str` == base tablename for results of analysis (network node geometry + accessibility attribute columns)
- `output_schema: str` == schema to store output analysis result + QAQC layers

### Optional Arguments

The following arguments are optional, and will use defaults unless overridden:

#### General Analysis Settings

- `walking_mph: float = 2.5` == assumed pedestrian walking speed in miles-per-hour
- `max_minutes: float = 45` == distance(/time) threshold to the analysis
- `epsg: int = 26918` == spatial data projection
- `num_pois: int = 3` == number of POIs to analyze when provided with groups (i.e. multiple features per ID)
- `poi_match_threshold: int = 45` == maximum allowable snapping distance between POI and node layers

#### Execution Control

- `run_on_create: bool = True` == flag that controls whether or not the analysis is run when the analysis object is instantiated from the class

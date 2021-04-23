# :material-walk: Accessibility

The core logic for the accessibility analysis is encapsulated within the [`RoutableNetwork`](https://github.com/dvrpc/network-routing/blob/master/network_routing/accessibility/routable_network.py#L10) class.

---

## Python usage

To use directly in a Python process, import the `RoutableNetwork` class from the `network_routing` module and instantiate the class with keyword arguments

```python
>>> from network_routing import RoutableNetwork, db_connection
>>> db = db_connection()
>>> my_kwargs = {"poi_table_name": "my_table_name", "poi_id_column": "id_colname"}
>>> net = RoutableNetwork(db, "schema_name", **my_kwargs)
```

---

## CLI usage

A command-line-interface is provided under the top-level name `access`.

To execute the default analysis, run:

```bash
access sw-default
```

There are a number of configurations, all of which can be found within [`network_routing/accessibility/cli.py`](https://github.com/dvrpc/network-routing/blob/master/network_routing/accessibility/cli.py).

You can also see a list of all available configurations by running `access --help`

```bash
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

---

## High-level overview

The following pseudo-code describes the flow of events when a `RoutableNetwork` is created:

### Setup

- Get a list of all "themes", i.e. unique POI categories
- Assign start/end node ID values to each segment
- Calculate the travel time cost to traverse each segment

### Construct network

- Get geodataframes of edge and node layers out of SQL
- Build a `pandana.Network()` and precompute it

### Analyze POIs

- Calculate each POI category by adding the POI category to the networkand computing distances to the N-nearest POIs for every node in the network
- Combine the results of each single POI analysis into one table
- Save table to database and generate geotable with results tied to geometries
- Clean up by moving results to a new schema and deleting temp QAQC tables

---

::: network_routing.accessibility.routable_network

# :material-walk: Accessibility

## Quickstart

All accessibility analyses can be called with the CLI prefix `access`. To execute the default analysis, run:

```bash
> access sw-default
```

---

## Workflow

The core logic for the accessibility analysis is encapsulated within the [`RoutableNetwork`](https://github.com/dvrpc/network-routing/blob/master/network_routing/accessibility/routable_network.py#L10) class:

#### Step 1: Setup

- Get a list of all unique POI categories
- Assign start/end node ID values to each segment
- Calculate the travel time cost to traverse each segment

#### Step 2: Construct network

- Extract edge and node geodataframes from SQL
- Build a `pandana.Network()` and precompute it

#### Step 3: Analyze POIs

- Calculate each POI category by adding the POI category to the network and computing distances to the N-nearest POIs for every node in the network
- Combine the results of each single POI analysis into one table
- Save table to database and generate geotable with results tied to geometries
- Clean up by moving results to a new schema and deleting temp QAQC tables

---

## Python usage

To use directly in a Python process, import the `RoutableNetwork` class from the `network_routing` module and instantiate the class with keyword arguments

```python
>>> from network_routing import RoutableNetwork, db_connection
>>> db = db_connection()
>>> my_kwargs = {"poi_table_name": "my_table_name", "poi_id_column": "id_colname"}
>>> net = RoutableNetwork(db, "schema_name", **my_kwargs)
```

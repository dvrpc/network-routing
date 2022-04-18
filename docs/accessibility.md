# :material-grid: Network Analysis Methodology

## Introduction

The core logic for the accessibility analysis is encapsulated within the [`RoutableNetwork`](https://github.com/dvrpc/network-routing/blob/master/network_routing/accessibility/routable_network.py#L10) class.

This code builds upon the [`pandana`](https://github.com/UDST/pandana) library, adding the ability to read data inputs from PostgreSQL and to save analysis results back to PostgreSQL.

---

## Workflow

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

To use this code directly in a Python process, import the `RoutableNetwork` class from the `network_routing` module, instantiate the class with keyword arguments, and run the command to compute every POI result into a single output table in postgres:

```python

from network_routing import pg_db_connection
from network_routing.accessibility.routable_network import RoutableNetwork

db = pg_db_connection()

arguments = {
    "edge_table_name": "pedestriannetwork_lines",
    "node_table_name": "nodes_for_sidewalks",
    "node_id_column": "sw_node_id",
    "poi_table_name": "regional_transit_with_accessscore",
    "poi_id_column": "category",
    "output_table_name": "regional_transit_stops",
    "output_schema": "sw_defaults",
    "max_minutes": 120,
    "poi_match_threshold": 152,
}

net = RoutableNetwork(db, **arguments)
net.compute_every_poi_into_one_postgres_table()
```

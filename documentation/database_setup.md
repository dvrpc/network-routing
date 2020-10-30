# Database Setup


All of the following commands must be executed within [the project's
Python environment](dev_environment.md). Activate it before moving on.

```bash
(base) $ conda activate network_routing
(network_routing) $
```

## Build the initial database

The most effective way to extract the necessary data is to access it
from a computer behind DVRPC's firewall:

```bash
(network_routing) $ python .\database\initial_setup.py
```

This process imports the following datasets from DVRPC's GIS database:
- pedestriannetwork_lines
- pedestriannetwork_points
- passengerrailstations
- transitparkingfacilities
- points_of_interest
- municipalboundaries

It then manipulates some of these datasets to create a few new ones:
- regional_counties
- regional_pois

[All transit stops in the region](https://github.com/aaronfraint/philly-transit-data) are then imported:
- regional_transit_stops

Finally, OpenStreetMap data is downloaded via [`osmnx`](https://github.com/gboeing/osmnx) and imported to the SQL database:
- osm_edges_drive
- osm_nodes_drive

## Save/load a snapshot of the database

The analysis code runs substantially slower on Windows machines. To save
a copy of the database for use on another computer:

```bash
(network_routing) $ db-export freeze
```

This process will attempt to place it into a GoogleDrive folder, and will ask you to create the folder first if it doesn't exist yet.


To load up the frozen database on another machine:
```bash
(network_routing) $ db-import from-dumpfile network_routing_raw
```
Note: it will load the dumpfile into the database identified with the `DB_NAME`
environment variable. It will overwrite the database if one already existed with that name. Proceed with caution.

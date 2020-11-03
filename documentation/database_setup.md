# Database Setup


All of the following commands must be executed within [the project's
Python environment](dev_environment.md). Activate it before moving on.

```bash
(base) $ conda activate network_routing
(network_routing) $
```

## Download data for the initial database

There's a few ways to get the database spooled up for analysis:

### 1) From a DVRPC workstation, run:

```
python database/initial_setup.py
```

### 2) From any other computer, run:

```
python database/setup_from_portal.py
```

Note: This will only work if `wget` is installed and available on the system path.

### 3) Load a snapshot of the database

The analysis code runs substantially slower on Windows machines. To save
a copy of the database for use on another computer:

```bash
db-export freeze
```

This process will attempt to place it into a GoogleDrive folder, and will ask you to create the folder first if it doesn't exist yet. If you want to see a list of all available options provided with this command, run `db-export freeze --help`


To load up the frozen database named `SNAPSHOT` on a new machine, run:
```
db-import from-dumpfile SNAPSHOT
```

Note: it will load the dumpfile into the database identified with the `DB_NAME`
environment variable. It will overwrite the database if one already existed with that name. Proceed with caution.


## Generate topologically-sound nodes for the sidewalk and OSM edges

Generate a node layer for the OSM edges:

```bash
transit make-nodes
```

Generate a node layer for the Sidewalk data:

```bash
sidewalk make-nodes
```

These processes output tables named `nodes_for_osm` and `nodes_for_sidewalks`, respectively. Both are stored within the `public` schema.

## Data in initial database:

This process imports the following datasets from DVRPC's GIS database:
- pedestriannetwork_lines
- pedestriannetwork_points
- passengerrailstations
- transitparkingfacilities
- points_of_interest
- municipalboundaries
- ipd_2018

It then manipulates some of these datasets to create a few new ones:
- regional_counties
- regional_pois

[All transit stops in the region](https://github.com/aaronfraint/philly-transit-data) are then imported:
- regional_transit_stops

Finally, OpenStreetMap data is downloaded via [`osmnx`](https://github.com/gboeing/osmnx) and imported to the SQL database:
- osm_edges_drive
- osm_nodes_drive

# Database

The Python interface to the PostgreSQL/PostGIS datastore is managed by `PostgreSQL` class defined within
[`postgis_helpers`](https://github.com/aaronfraint/postgis-helpers), and a method to connect to the database is provided with a top-level import.

To use this module within Python, import the `db_connection` function from `network_routing` and instantiate it:

```Python
>>> from network_routing import db_connection
>>> db = db_connection()
```

---

## Quickstart

All of the necessary database processes can be called by the CLI with the command `db`

To get up and running with this project, execute the following commands from your terminal:

```bash
conda activate network_routing
db build-initial
db build-secondary 1
db build-secondary 2
db make-nodes-for-edges
```

---

## CLI documentation

To see all available commands, run `db --help`

```
Usage: db [OPTIONS] COMMAND [ARGS]...

  The command 'db' is used to run data import & export processes

Options:
  --help  Show this message and exit.

Commands:
  build-initial         Roll a brand-new database for with the...
  build-secondary       Update the db as defined by PATCH NUMBER
  export-geojson        Save a group of .geojson files to be tiled for...
  export-shapefiles     Export a set of shapefiles identified by EXPORT_NAME
  make-nodes-for-edges  Generate topologically-sound nodes for the...
  make-vector-tiles     Turn GeoJSON files into .mbtiles format
```

### Setup commands

`db build-initial`

- Create a brand new database
- If behind DVRPC's firewall it will connect directly to the source data's SQL database
- If run outside the firewall it will attemp to use `wget` to download the data via DVRPC's ArcGIS Portal

`db build-secondary NUMBER`

- Run a secondary data import process identified with an integer
- For an example, see [`setup_01_updated_ridescore_inputs.py`](https://github.com/dvrpc/network-routing/blob/master/network_routing/database/setup/setup_01_updated_ridescore_inputs.py)

`db make-nodes-for-edges`

- Generate topologically-sound node layers for `pedestriannetwork_lines`, `osm_edges_all`, and `osm_edges_drive`

### Export commands

`db export-geojson ANALYSIS_NAME`

- Export a set of geojson files, indicated by `ANALYSIS_NAME`
- Options include: `ridescore` and `gaps`
- Output folder is `FOLDER_DATA_PRODUCTS`

`db make-vector-tiles FILENAME`

- Generate a tileset named `FILENAME` from a folder full of geojson files
- Files are read from `FOLDER_DATA_PRODUCTS`

`db export-shapefiles EXPORT_NAME`

- Export a set of shapefiles that others will edit manually
- Options include: `manual_edits` and `ridescore_downstream_analysis`

# `network_routing.database`

The Python interface to the PostgreSQL/PostGIS datastore is managed by [`postgis_helpers.PostgreSQL`](https://github.com/aaronfraint/postgis-helpers), and a method to connect to the database is provided with a top-level import:

```python
from network_routing import db_connection

db = db_connection()
```

## CLI

All of the necessary database processes can be called by the CLI with the command `db`

### Setup commands

- `db build-initial`
  - Create a brand new database
  - If behind DVRPC's firewall it will connect directly to the source data's SQL database
  - If run outside the firewall it will attemp to use `wget` to download the data via DVRPC's ArcGIS Portal
- `db build-secondary NUMBER`
  - Run a secondary data import process identified with an integer
  - See [./setup/setup_01_updated_ridescore_inputs.py](./setup/setup_01_updated_ridescore_inputs.py) for an example
- `db make-nodes-for-edges`
  - Generate topologically-sound node layers for `pedestriannetwork_lines` and `osm_edges_all`

### Export commands

- `db export-geojson ANALYSIS_NAME`
  - Export a set of geojson files, indicated by `ANALYSIS_NAME`
  - Options include: `ridescore` and `gaps`
  - Output folder is `FOLDER_DATA_PRODUCTS`
- `db make-vector-tiles FILENAME`
  - Generate a tileset named `FILENAME` from a folder full of geojson files
  - Files are read from `FOLDER_DATA_PRODUCTS`

### Other commands

- `db export-shapefiles EXPORT_NAME`
  - Export a set of shapefiles that others will edit manually
  - Options include: `manual_edits` and `ridescore_downstream_analysis`

## `db --help`

To see all available commands, run `db --help`

```bash
> db --help

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

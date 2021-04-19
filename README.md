# network-routing

Python package to create and analyze routable pedestrian networks.

The codebase is broken up into three primary modules, each with its own command-line-interface.

1. [`accessibility`](./accessibility) - where all network routing code can be found
2. [`database`](./database) - where all data I/O is defined
3. [`gaps`](./gaps) - where all other analysis / visualization steps are kept

## Setup

1. Clone the repo
2. `cd` into the new folder
3. Build the Python environment with `conda`

```bash
git clone https://github.com/dvrpc/network-routing.git
cd network-routing
conda env create -f environment.yml
```

4. Create a `.env` file wherever you intend to run the analysis from. It should look like this:

```
DB_NAME=my_database_name
DB_HOST=localhost
GDRIVE_ROOT=/Volumes/GoogleDrive/My Drive
```

5. In order to run any of the commands listed below, you'll need to activate the `conda` environment:

```bash
conda activate network_routing
```

## Database creation

All database interactions are handled by the command `db`. The full set of docs can be found [here](./network_routing/database). To get up and running:

```bash
db build-initial
db build-secondary 1
db make-nodes-for-edges
```

## Gap analyses

Classify OSM centerlines by sidewalk coverage

```bash
gaps classify-osm-sw-coverage
```

Generate a layer of connected sidewalk islands

```bash
gaps identify-islands
```

## Base accessibility analysis

Identify accessibility along the sidewalk network to the closest transit stop of every mode

```bash
access sw-default
```

## Ridescore accessibility analysis

Identify accessibility to each rail station using both the OSM and sidewalk networks

```bash
access osm-ridescore
access sw-ridescore
```

Process the results of the two analyses into a set of 1-mile isochrones

```bash
gaps isochrones
```

Generate a "sidewalkscore" for each of the input station points

```bash
gaps sidewalkscore
```

## Export data for webmap

Export geojson and associated tileset for the "base" + "gap" analyses

```bash
db export-geojson gaps
db make-vector-tiles sidewalk_gap_analysis
```

Export geojson and associated tileset for the "ridescore" analysis

```bash
db export-geojson ridescore
db make-vector-tiles ridescore_analysis
```

## Export shapefiles

A few shapefile export processes are defined, and available via:

```bash
db export-shapefiles EXPORT_NAME
```

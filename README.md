# network-routing

Python package to create and analyze routable pedestrian networks

Each step in the process is described in detail on its own page:

1. [Set up the development environment](documentation/dev_environment.md)
2. [Build the analysis database](documentation/database_setup.md)
3. [Execute the analysis for the RideScore project](documentation/analysis_ridescore.md)
4. [Execute the analysis for the Sidewalk Gaps project](documentation/analysis_sidewalk_gap.md)

To summarize the process:

## 1) Setup the dev environment

```bash
git clone https://github.com/dvrpc/network-routing.git
cd network_routing
conda env create -f env.yml
conda activate network_routing
```

... then create your `.env` file ...

## 2) Build the starter database

```bash
sidewalk make-nodes
transit make-nodes
```

## 3) Run the `SidewalkScore` analysis

```bash
transit calculate-sidewalk
transit calculate-osm
transit isochrones
transit sidewalkscore
```

## 4) Run the `Sidewalk Gaps` analysis

Analyze NJ:

```bash
sidewalk clip-data NJ
sidewalk analyze-segments nj
sideawlk analyze-network nj
```

Analyze PA:

```bash
sidewalk clip-data PA --buffer 2
sidewalk analyze-segments pa
sidewalk analyze-network pa
```

Analyze islands across the entire region:

```bash
sidewalk identify-islands
```

Prepare the final products:

```bash
sidewalk combine-centerlines
sidewalk scrub-osm-tags
sidewalk combine-transit-results
```

## 5) Generate vector tiles for the final webmap

Export the "sidewalk" and "transit" analyses via:

```bash
sidewalk export-geojson-for-webmap
sidewalk make-vector-tiles

transit export-geojson-for-webmap
transit make-vector-tiles
```

## TODO:

- Final hexagon summary

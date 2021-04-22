# Analysis Runs

## Base analysis

- Classify OSM "drive" segments by sidewalk coverage
- Run an accessibility analysis against regional transit stops (all modes)
- Cluster connected sidewalk segments into "islands" of connectivity

```bash
gaps classify-osm-sw-coverage
gaps identify-islands
access sw-default
```

## Ridescore analysis

- Run two access analyses against the same set of POIs (rail transit stops only), once using OSM "all" network and once using the sidewalk network
- Translate the results of the two access analyses into a set of isochrones
- Calculate the OSM vs Sidewalk accessible areas for each station and save result as new geo-table

```bash
access osm-ridescore
access sw-ridescore
gaps isochrones
gaps sidewalkscore
```

## MCPC analysis

... to do ...

## Visualize data

- Export SQL data to `.geojson` for all analyses
- Generate vector tiles in the `.mbtiles` format, for use in an external MapboxGL JS map

```bash
db export-geojson ridescore
db export-geojson gaps
db make-vector-tiles sidewalk_gap_analysis
```

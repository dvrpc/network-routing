# :material-sitemap: Analysis Runs

---

## Base

- Setup database
- Classify OSM "drive" segments by sidewalk coverage
- Run an accessibility analysis against regional transit stops (all modes)
- Cluster connected sidewalk segments into "islands" of connectivity

```bash
# Setup database
> db build-initial
> db build-secondary 1
> db build-secondary 2
> db build-secondary 3
> db make-nodes-for-edges

# Run base analysis
> gaps classify-osm-sw-coverage
> gaps identify-islands
> access sw-default
```

---

## Ridescore

- Run two access analyses against the same set of POIs (rail transit stops only), once using OSM "all" network and once using the sidewalk network
- Translate the results of the two access analyses into a set of isochrones
- Calculate the OSM vs Sidewalk accessible areas for each station and save result as new geo-table

```bash
> access osm-ridescore
> access sw-ridescore
> gaps isochrones
> gaps sidewalkscore
```

---

## MCPC

- Analyze sidewalk accessibility to the 3-nearest POIs of each type from the
  [Equity Through Access dataset](https://dvrpcgis.maps.arcgis.com/apps/MapSeries/index.html?appid=06eab792a06044f89b5b7fadeef660ba)

```bash
> access sw-eta
```

- To do: find/score gaps closest to schools

---

## Visualize data

- Export SQL data to `.geojson` for all analyses
- Generate vector tiles in the `.mbtiles` format, for use in an external MapboxGL JS map

```bash
> db export-geojson ridescore
> db export-geojson gaps
> db make-vector-tiles sidewalk_gap_analysis
```

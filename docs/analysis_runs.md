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
> db build-secondary 4
> db make-nodes-for-edges pedestriannetwork_lines

# Run base analysis
> gaps classify-osm-sw-coverage
> gaps identify-islands
> access sw-default
```

---

## Access Score

- Run three access analyses against the same set of rail transit stops: OSM "all" network (2 miles), low-stress bicycle network (2 miles), and sidewalk network (1 mile)
- Translate the results of the two access analyses into a set of isochrones
- Calculate the OSM vs Sidewalk accessible areas for each station and save result as new geo-table

- Generate the nodes necessary for the three analyses:

```bash
> db make-nodes-for-edges osm_edges_all_no_motorway
> db make-nodes-for-edges lowstress_islands
```

- Run all three analyses:

```bash
> access osm-access-score
> access lowstress-access-score
> access sw-access-score
```

- Generate line-based representation of the results:

```bash
> gaps accessscore-line-results
```

- If you want to generate isochrones of the results:

```bash
> gaps isochrones-accessscore
```

---

## Visualize data

- Export SQL data to `.geojson` for all analyses
- Generate vector tiles in the `.mbtiles` format, for use in an external MapboxGL JS map

```bash
> db export-geojson ridescore
> db export-geojson gaps
> db make-vector-tiles sidewalk_gap_analysis
```

---

## MCPC

- Analyze sidewalk accessibility to the 3-nearest POIs of each type from the
  [Equity Through Access dataset](https://dvrpcgis.maps.arcgis.com/apps/MapSeries/index.html?appid=06eab792a06044f89b5b7fadeef660ba)

```bash
> access mcpc-individual
> gaps isochrones-mcpc

> db make-nodes-for-edges improvements.montgomery_split

> db export-geojson mcpc
> db make-vector-tiles mcpc mcpc_v4
```

- To do: score gaps closest to each POI type

- To do: document gap creation process and before/after project comparison code

---

## PART

Analyze POIs in the Pottstown area.

``bash

> access part-sidewalk
> access part-osm
> gaps isochrones-part
> db export-geojson part

```

```

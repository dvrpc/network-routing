# :material-blur-off: Gaps

All commands within this module can be run with the prefix `gaps`

## Segment Analyses

Classify OSM centerlines by sidewalk coverage:

```bash
gaps classify-osm-sw-coverage
```

Identify islands of connectivity:

```bash
gaps identify-islands
```

## Data Visualization

Generate isochrones of the sidewalk- & OSM-based access analyses:

```bash
gaps isochrones
```

Calculate the "sidewalkscore" for the RideScore transit stations:

```bash
gaps sidewalkscore
```

Simplify OSM `highway` tags:

This process adds a new column named `hwy_tag` to the table `data_viz.osm_sw_coverage`

The column is then populated with a single, clean tag. If multiple tags are present,
the tag higher in the hierarchy will be used (e.g. `"{trunk, tertiary}" -> "trunk"` ).

```bash
gaps scrub-osm-tags
```

# :material-blur-off: Gaps

## Quickstart

All commands within this module can be run with the prefix `gaps`

---

## Segment Analyses

`> gaps classify-osm-sw-coverage`

- Classify OSM centerlines by sidewalk coverage

`> gaps identify-islands`

- Identify islands of connectivity

---

## Data Visualization

`> gaps isochrones`

- Generate isochrones of the sidewalk- & OSM-based access analyses

`> gaps sidewalkscore`

- Calculate the "sidewalkscore" for the RideScore transit stations

`> gaps scrub-osm-tags`

- Simplify OSM `highway` tags
- This process adds a new column named `hwy_tag` to the table `data_viz.osm_sw_coverage`
- The column is then populated with a single, clean tag. If multiple tags are present, the tag higher in the hierarchy will be used (e.g. `"{trunk, tertiary}" -> "trunk"` )

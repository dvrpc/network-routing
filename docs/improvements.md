# :material-map-marker-path: Improvements

All commands within this module can be run with the prefix `improvements`

---

## Scripts

`> improvements draw-missing-network-links COUNTYNAME`

- For the provided county, draw lines for all road network segments that do not have complete sidewalk coverage. This will draw too many features, but that will be fixed with the next command.
- Before you can run this command you need to run `gaps classify-osm-sw-coverage`

`> improvements feature-engineering ERASE SPLIT`

- Clean up the output of the prior script by erasing newsidewalk features near existing sidewalks.
- Use the flag `--erase` to run the erase script
- Use the flag `--split` if you intend to incorporate the output into a routable network
- After running this script, the outputs can be exported with `db export-geojson regional_gaps`

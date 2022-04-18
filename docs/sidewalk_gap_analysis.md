# :fontawesome-solid-person-walking-arrow-right: Sidewalk Gap Analysis

## Generate data for the [Sidewalk Gap Analysis Explorer](https://www.dvrpc.org/webmaps/sidewalk-gaps/)

All of the analyses and export procedures needed for the Sidewalk Gap Analysis Explorer can be run with the following command:

```
make sidewalk-gaps-map
```

This command will run for a number of hours, and bundles a number of commands in sequence.

---

## Bundled Commands

Identify the sidewalk coverage of every OSM centerline:

`gaps classify-osm-sw-coverage`

---

Clean up the OSM feature tags to help filter the output for the webmap:

`gaps scrub-osm-tags`

---

Identify portions of the sidewalk network that form discrete "islands":

`gaps identify-islands`

---

Run a routing analysis to transit stops of all modes across the region:

`access sw-default`

---

Run a routing analysis to all public and private schools across the region:

`access eta-schools`

---

Export geojson data for the school, transit, island, and centerline analyses:

`db export-geojson gaps`

---

Identify the walksheds around every rail station across the region using the sidewalk network and then the OpenStreetMap network:

`access sw-access-score`

`access osm-access-score`

---

Turn the OSM and sidewalk rail station analyses into polygon isochrones:

`gaps isochrones-accessscore`

---

Export the rail station isochrones to geojson:

`db export-geojson accessscore`

---

Turn the exported geojson files into a single vector tileset for the web map:

`db make-vector-tiles gaps sidewalk_gap_analysis`

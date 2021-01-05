# RideScore

Travelsheds are identified for each passenger rail station in the DVRPC region, using both the sidewalk network and the OSM driving network. These two travelsheds are transformed into isochrones for each station, illustrating the similarity or difference between the two accessibility profiles.

## Before we start:

Set up your [development environment](dev_environment.md)
and [build the analysis database](database_setup.md) first.

All commands related to this project are prefixed with `transit`. To see a list of all available commands, run: `transit --help`

## Run [the analysis](../transit_access/network_analysis.py) against both networks:

### Start with the sidewalk network:

```bash
transit calculate-sidewalks
```

The results of this analysis will end up in a schema named `rs_sw`

### Then analyze the OpenStreetMap network:

```bash
transit calculate-osm
```

The results of this analysis will end up in a schema named `rs_osm`

## [Generate isochrones](../transit_access/ridescore_isochrones.py#L7) from the sidewalk & OSM analysis runs:

```bash
transit isochrones
```

The output is a polygon table named `ridescore_isos` in a schema named `data_viz`

## Calculate the ["sidewalkscore"](../transit_access/ridescore_isochrones.py#L76) for each rail station:

```bash
transit sidewalkscore
```

The output is a point table named `sidewalkscore` in a schema named `data_viz`.

## Export vector tiles for webmap

To generate vector tiles with the analysis outputs, run:

```bash
transit export-geojson-for-webmap
transit make-vector-tiles
```

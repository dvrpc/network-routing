# RideScore

Travelsheds are identified for each passenger rail station in the DVRPC region, using both the sidewalk network and the OSM driving network. These two travelsheds are transformed into isochrones for each station, illustrating the similarity or difference between the two accessibility profiles.

## Run the sidewalk analysis:

```bash
transit calculate-sidewalks
```

The results of this analysis will end up in a schema named `rs_sw`

## Run the OSM analysis:

```bash
transit calculate-osm
```

The results of this analysis will end up in a schema named `rs_osm`

## Generate isochrones from the sidewalk & OSM analysis runs:

```bash
transit isochrones
```

The output is a polygon table named `ridescore_isos` in a schema named `data_viz`



## Calculate the "sidewalkscore" for each rail station:


```bash
transit sidewalkscore
```

The output is a point table named `sidewalkscore` in a schema named `data_viz`

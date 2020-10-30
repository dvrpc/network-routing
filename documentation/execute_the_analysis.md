# Analysis Execution


## Prepare node layers

Generate a node layer for the OSM edges:

```bash
(network_routing) $ transit make-nodes
```

Generate a node layer for the Sidewalk data:

```bash
(network_routing) $ sidewalk make-nodes
```

## RideScore

Travelsheds are identified for each passenger rail station in the DVRPC region, using both the sidewalk network and the OSM driving network. These two travelsheds are transformed into isochrones for each station, illustrating the similarity or difference between the two accessibility profiles.

Run the sidewalk analysis:

```bash
(network_routing) $ transit calculate-sidewalks
```

Run the OSM analysis:
```bash
(network_routing) $ transit calculate-osm
```

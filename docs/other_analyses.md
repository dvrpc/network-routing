# :material-code-braces: Other Analyses

## Network analysis configurations

There are a number of other accessibility analyses defined within

[`./network_routing/accessibility/cli.py`](https://github.com/dvrpc/network-routing/blob/master/network_routing/accessibility/cli.py)

These can be run in a one-off fashion using the `access` command. For example, to execute the analysis for the PART project you can run:

```
access part-sidewalk
access part-osm
```

Each of these configurations defines the network edge table, the Point-of-Interest table, and other analysis parameters like search distance, snap tolerance, and output schema and table names.

## Draw missing sidewalk segments

To draw the missing sidewalks (i.e. "gaps") run the following command:

```
improvements draw-missing-network-links COUNTYNAME
```

Replace `COUNTYNAME` with the name of the county you want to analyze, like "`Montgomery`", "`Camden`", etc.

Note: this command can only be run after first running `gaps classify-osm-sw-coverage`

The result of this script is a set of lines that overshoots what's needed. To clean this dataset up, run the following command:

```
improvements feature-engineering --erase
```

After running this script, the outputs can be exported with:

```
db export-geojson regional_gaps
```

# Sidewalk Gap Analysis Process

## Before we start:

Set up your [development environment](dev_environment.md)
and [build the analysis database](database_setup.md) first.

All commands related to this project are prefixed with `sidewalk`. To see a list of all available commands, run: `sidewalk --help`

## [Extract Data](../sidewalk_gaps/extract_data)

- Clip the datasets by to the NJ region with `sidewalk clip-data NJ`. The result of this is a new database schema for each state, and the subsequent analyses will take places within these state-specific schemas.

- Repeat for PA with `sidewalk clip-data PA --buffer 2`. Note the use of a 2-meter buffer here. There are a few sidewalk segments that extend beyond the county boundary and we'll miss their respective nodes when clipping without a buffer.

## [Segment Analysis](../sidewalk_gaps/segments)

### Classify centerlines by sidewalk coverage ratio

- Classify centerlines with the amount of sidewalk coverage in NJ with `sidewalk analyze-segments nj`

- Repeat for PA with `sidewalk analyze-segments pa`. Runtime is ~4 hrs for NJ and double for PA. This is a one-time execution, so kick it off at the end of a workday and let them run concurrently over the evening.

### Merge connected sidewalks into distinct 'islands'

- Create a layer where all intersecting sidewalk segments are merged into a single feature with `sidewalk identify-islands`

- This can be run against any schema by adding `-s schema_name`, although it's best to run against the regional data to capture bi-state islands

## [Network Analysis](../sidewalk_gaps/accessibility)

- Execute a network-based accessibility analysis for NJ with `sidewalk analyze-network nj`

- Repeat for PA with `sidewalk analyze-network pa`

## [Prepare & Export Data Products for Visualization](../sidewalk_gaps/data_viz)

- Merge the PA and NJ centerlines together with `sidewalk combine-centerlines`

- Clean up the OSM highway tags with `sidewalk scrub-osm-tags`

- **Need to update:** Create a hexagon layer that covers the region, and identify the following conditions:

  - number of unique islands
  - difference between high/low connectivity values
  - length of centerlines that are missing sidewalks

- **_The results of this analytic process are exported to file with (TODO - wire up command)._** These outputs are used in interactive webmaps. The code for these maps are contained within another GitHub repository - https://github.com/dvrpc/sidewalk-data-viz

# Analysis Process

This python module includes a command-line-interface (CLI). To use the CLI you'll need to open a terminal and activate the environment with ``conda activate network_analysis``


Commands will begin with ``sidewalk`` or `transit`. To see a list of all available sub-commands, use ``sidewalk --help`` or `transit --help`.


## [Database Setup](../database)

1) There's a few ways to get the database spooled up for analysis:

    1a) From a DVRPC workstation, run `python database/initial_setup.py`

    1b) Load up a full `SNAPSHOT` of the database with: `db-import from-dumpfile SNAPSHOT`

    1d) Build a fresh database by loading data directly from DVRPC's ArcIGS REST Portal. To do this, run: `python database/setup_from_portal.py`


2) Generate the sidewalk node layer with ``sidewalk make-nodes``.

3) Generate the OSM node layer with ``transit make-nodes``.


## [Sidewalk Analysis](../sidewalk_gaps)

### [Extract Data](../sidewalk_gaps/extract_data)


- Clip the datasets by to the NJ region with ``sidewalk clip-data NJ``. The result of this is a new database schema for each state, and the subsequent analyses will take places within these state-specific schemas.


- Repeat for PA with ``sidewalk clip-data PA --buffer 2``. Note the use of a 2-meter buffer here. There are a few sidewalk segments that extend beyond the county boundary and we'll miss their respective nodes when clipping without a buffer.


### [Segment Analysis](../sidewalk_gaps/segments)


- Classify centerlines with the amount of sidewalk coverage in NJ with ``sidewalk analyze-segments nj`` 

- Repeat for PA with ``sidewalk analyze-segments pa``. Runtime is ~4 hrs for NJ and double for PA. This is a one-time execution, so kick it off at the end of a workday and let them run concurrently over the evening.

- Create a layer where all intersecting sidewalk segments are merged into a single feature with ``sidewalk identify-islands nj``

- Repeat for PA with ``sidewalk identify-islands pa``


### [Network Analysis](../sidewalk_gaps/accessibility)


- Execute a network-based accessibility analysis for NJ with ``sidewalk analyze-network nj``

- Repeat for PA with ``sidewalk analyze-network pa``


### [Prepare & Export Data Products for Visualization](../sidewalk_gaps/data_viz)

- Create a hexagon layer that covers the region, and identify the following conditions:
    - number of unique islands
    - difference between high/low connectivity values
    - length of centerlines that are missing sidewalks


- The results of this analytic process are exported to file with (TODO - wire up command). These outputs are used in interactive webmaps. The code for these maps are contained within another GitHub repository - https://github.com/dvrpc/sidewalk-data-viz


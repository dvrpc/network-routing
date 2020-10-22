# Analysis Process

This python module includes a command-line-interface (CLI). To use the CLI you'll need to open a terminal and activate the environment with ``conda activate network_analysis``


All actions will begin with the command ``sidewalk``. To see a list of all available sub-commands, use ``sidewalk --help``.


## [Database Setup](../sidewalk_gaps/db_setup)


1) Build a PostgreSQL database from DVRPC's data sources with ``sidewalk db-setup``. This must be done from a workstation behind DVRPC's firewall. Most datasets are loaded directly from DVRPC's GIS SQL server, and this requires a PostGIS connection defined with the name ``dvrpc_gis``. In addition, there are a few flat files that must be loaded from the ``U:\`` drive, and as a result the ``PROJECT_ROOT`` must be defined in the ``.env`` file. For more info on this, review the [dev environment setup process](dev_environment.md).


2) Save the SQL database to text file with ``sidewalk db-freeze``. If ``GDRIVE_ROOT`` is configured, it will automatically be placed in the proper cloud folder. If unspecified it will be in the active directory and must be manually copied to Google Drive.


3) Load the text file onto your machine of choice with ``sidewalk db-load``.


4) Generate the node layer with ``sidewalk make-nodes``.


## [Extract Data](../sidewalk_gaps/extract_data)


5) Clip the datasets by to the NJ region with ``sidewalk clip-data NJ``. The result of this is a new database schema for each state, and the subsequent analyses will take places within these state-specific schemas.


6) Repeat for PA with ``sidewalk clip-data PA --buffer 2``. Note the use of a 2-meter buffer here. There are a few sidewalk segments that extend beyond the county boundary and we'll miss their respective nodes when clipping without a buffer.


## [Segment Analysis](../sidewalk_gaps/segments)


7) Classify centerlines with the amount of sidewalk coverage in NJ with ``sidewalk analyze-segments nj`` 

8) Repeat for PA with ``sidewalk analyze-segments pa``. Runtime is ~4 hrs for NJ and double for PA. This is a one-time execution, so kick it off at the end of a workday and let them run concurrently over the evening.

9) Create a layer where all intersecting sidewalk segments are merged into a single feature with ``sidewalk identify-islands nj``

10) Repeat for PA with ``sidewalk identify-islands pa``


## [Network Analysis](../sidewalk_gaps/accessibility)


11) Execute a network-based accessibility analysis for NJ with ``sidewalk analyze-network nj``

12) Repeat for PA with ``sidewalk analyze-network pa``

13) Summarize the network analysis results with a hexagon overlay that identifies locations where connectivity within the sidewalk network could be improved. (TODO)


## [Prepare & Export Data Products for Visualization](../sidewalk_gaps/data_viz)

14) Create a hexagon layer that covers the region, and identify the following conditions:
    - number of unique islands
    - difference between high/low connectivity values
    - length of centerlines that are missing sidewalks


15) The results of this analytic process are exported to file with (TODO - wire up command). These outputs are used in interactive webmaps. The code for these maps are contained within another GitHub repository - https://github.com/dvrpc/sidewalk-data-viz


## Full Analysis Sequence

```bash
# Build the development environment using a terminal w/ conda
(base) > git clone https://github.com/dvrpc/network-routing.git
(base) > cd network_routing
(base) > conda env create -f env.yml
(base) > conda activate network_routing
(network_routing) > conda activate network_routing

# Prepare the database
(network_routing) > sidewalk db-setup
(network_routing) > sidewalk make-nodes

# Analyze the NJ side of the region
(network_routing) > sidewalk clip-data NJ
(network_routing) > sidewalk analyze-segments nj
(network_routing) > sidewalk identify-islands nj
(network_routing) > sidewalk analyze-network nj

# Analyze the PA side of the region
(network_routing) > sidewalk clip-data PA --buffer 2
(network_routing) > sidewalk analyze-segments pa
(network_routing) > sidewalk identify-islands pa
(network_routing) > sidewalk analyze-network pa
```

## Notes

Steps 2 and 3 are optional and all of this could be completed on a DVRPC workstation. However, some steps require tens of thousands of SQL queries, and you'll get substantially better performance using MacOS (and a SSD).
# Analysis Process

This python module includes a command-line-interface (CLI). To use the CLI you'll need to open a terminal and activate the environment with ``conda activate network_analysis``


All actions will begin with the command ``sidewalk``. To see a list of all available sub-commands, use ``sidewalk --help``.


## [Database Setup](../sidewalk_gaps/db_setup)


1) Build a PostgreSQL database from DVRPC's data sources with ``sidewalk db-setup``. This must be done from a workstation behind DVRPC's firewall. Most datasets are loaded directly from DVRPC's GIS SQL server, and this requires a PostGIS connection defined with the name ``dvrpc_gis``. In addition, there are a few flat files that must be loaded from the ``U:\`` drive, and as a result the ``PROJECT_ROOT`` must be defined in the ``.env`` file. For more info on this, review the [dev environment setup process](dev_environment.md).


2) Save the SQL database to text file with ``sidewalk db-freeze``. If ``GDRIVE_ROOT`` is configured, it will automatically be placed in the proper cloud folder. If unspecified it will be in the active directory and must be manually copied to Google Drive.


3) Load the text file onto your machine of choice with ``sidewalk db-load``.


4) Merge the sidewalk lines with the existing trail network, splitting lines from each layer anywhere that they intersect. (UNDER DEVELOPMENT)


5) Generate the node layer with ``sidewalk generate-nodes``


## [Extract Data](../sidewalk_gaps/extract_data)


6) Clip the datasets by state with ``sidewalk clip-data NJ`` and ``sidewalk clip-data PA``. The result of this is a new database schema for each state, and the subsequent analyses will take places within these state-specific schemas.


## [Segment Analysis](../sidewalk_gaps/segments)


7) Classify centerlines with the amount of sidewalk coverage with ``sidewalk analyze-segments nj`` and ``sidewalk analyze-segments pa``. Runtime is ~4 hrs for NJ and double for PA. This is a one-time execution, so kick it off at the end of a workday and let them run concurrently over the evening.


## [Network Analysis](../sidewalk_gaps/accessibility)


8) Execute a network-based accessibility analysis with ``sidewalk analyze SCHEMA``

9) Summarize the network analysis results with a hexagon overlay that identifies locations where connectivity within the sidewalk network could be improved. (TODO)


## [Export Data Products for Visualization](../sidewalk_gaps/data_viz)


10) The results of this analytic process are exported to file with (TODO - wire up command). These outputs are used in interactive webmaps. The code for these maps are contained within another GitHub repository - https://github.com/dvrpc/sidewalk-data-viz




## Notes

Steps 2 and 3 are optional and all of this could be completed on a DVRPC workstation. However, some steps require tens of thousands of SQL queries, and you'll get substantially better performance using MacOS (and a SSD).
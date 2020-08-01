# ``sidewalk_gaps.db_setup``

Create a database that will become the basis of this analysis.

Import data from DVRPC's feature server:
- sidewalk lines and points
- PA centerlines
- points of interest
- municipal boundaries

Import some additional data from file:
- NJ centerlines
- microzone polygons
- sidewalk network nodes

Load a PSQL function that returns the median of an array.

Use imported geodata to generate a few new layers:
- merge DVRPC municipalities into county polygons
- clip the POI layer by DVRPC counties

## Usage

Three command-line utilities are available:


Create a new database, in this example named ``my_db_name``
```
sidewalk db-setup --database my_db_name --folder /my/src/data/folder
```

Freeze a database into a ``.SQL`` text file
```
sidewalk db-freeze --database my_db_name --folder /my/db/backup/folder
```


Load a previously-created database
```
sidewalk db-load --database my_db_name --folder /my/db/backup/folder
```

# ``sidewalk_gaps.db_setup``

Create a database that will become the basis of this analysis.

### 1) Import data from DVRPC's feature server
- sidewalk lines and points
- PA centerlines
- points of interest
- municipal boundaries

### 2) Import extra data from file
- NJ centerlines
- microzone polygons
- sidewalk network nodes

### 3) Use imported geodata to generate some new layers
- merge DVRPC municipalities into county polygons
- clip the POI layer by DVRPC counties

## CLI Usage

Three command-line utilities are available.

All three commands take two arguments:
- Database name, via ``-d`` or ``--database``
- Folder name, via ``-f`` or ``--folder``


1) Create a new database, in this example named ``my_db_name``
```
sidewalk db-setup -d my_db_name
```

2) Freeze a database into a ``.SQL`` text file
```
sidewalk db-freeze -d my_db_name -f /my/db/backup/folder
```


3) Load a previously-created database
```
sidewalk db-load -d my_db_name -f /my/db/backup/folder
```

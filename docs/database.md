# :material-database: Prepare the Database

## Import the starter datasets from the web

Import the sidewalk and OpenStreetMap networks as well as a few other datasets from DVRPC's GIS server:

```
make prepare-initial-database
```

---

## Import the additional datasets from Google Drive

There are a number of shapefiles necessary for some of the analysis configurations that have been added to a shared Google Drive folder.

These files are organized under sub-folders within `Shared drives/network-routing-repo-data/data/inputs`. Make sure you have this folder synced to your computer with all files available offline.

To import these files and create the network nodes necessary for the routing analyses, run the following command:

```
make prepare-for-analysis
```

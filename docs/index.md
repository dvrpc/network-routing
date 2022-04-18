# :material-map-marker-path: `network-routing`

## About

This is the documentation for `network_routing`, a Python package developed by DVRPC to produce the datasets shown in the [Sidewalk Gap Analysis Explorer](https://dvrpc.github.io/sidewalk-data-viz/).

This work was conducted using DVRPC’s pedestrian facilities inventory, a GIS dataset that inventories sidewalks, curb ramps, and crosswalks across the nine-county Greater Philadelphia region. Explore the data and help plan for a pedestrian-friendly future at [walk.dvrpc.org](https://walk.dvrpc.org/).

This codebase facilitates the creation and analysis of routable networks, using any topological network dataset including:

- OpenStreetMap
- DVRPC's sidewalk network
- DVRPC's Level of Traffic Stress network

Data for the analysis is stored in a [`PostgreSQL/PostGIS`](https://postgis.net/) database and the process is scripted using [`Python`](https://www.python.org).

The codebase is broken up into four primary modules, each with its own command-line-interface (CLI):

- `db` controls all data I/O
- `access` manages all accessibility/routing analyses
- `gaps` handles analysis processes that don't use network routing
- `improvements` generates tables showing the missing gaps in the sidewalk network

It builds on top of a variety of libraries, including `pandana`, `pg_data_etl`, `osmnx`, `geopandas`/`pandas`, `geoalchemy2`/`sqlalchemy`, & `psycopg2`

---

## Software Requirements

This codebase requires the following software:

- [`git`](https://git-scm.com/)
- [Python 3](https://docs.conda.io/en/latest/index.html)
- [PostgreSQL](https://www.postgresql.org/) & [PostGIS](https://postgis.net/)

Optional software includes:

- `make` if you'd like to take advantage of the bundled sets of commands defined in the `Makefile`
- [`tippecanoe`](https://github.com/mapbox/tippecanoe) is needed if you'd like to generate vector tile outputs for a webmap

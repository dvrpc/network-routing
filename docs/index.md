# :material-map-marker-path: `network-routing`

## About

This is the documentation for `network_routing`, a Python package developed by DVRPC to produce the datasets shown in the [Sidewalk Gap Analysis Explorer](https://dvrpc.github.io/sidewalk-data-viz/).

This work was conducted using DVRPC’s pedestrian facilities inventory, a GIS dataset that inventories sidewalks, curb ramps, and crosswalks across the nine-county Greater Philadelphia region. Explore the data and help plan for a pedestrian-friendly future at [walk.dvrpc.org](https://walk.dvrpc.org/).

---

## Quickstart

`network_routing` facilitates the creation and analysis of routable pedestrian networks, using
both OpenStreetMap data as well as DVRPC's sidewalk data inventory. Data for the analysis is stored in a [`PostgreSQL/PostGIS`](https://postgis.net/) database and the process is scripted using [`Python`](https://www.python.org).

The codebase is broken up into three primary modules, each with its own command-line-interface (CLI):

- [`db`](./database.md) controls all data I/O
- [`access`](./accessibility.md) manages all accessibility/routing analyses
- [`gaps`](./gaps.md) handles all other analysis processes

It builds on top of a variety of libraries, including `pandana`, `postgis_helpers`, `osmnx`, `geopandas`/`pandas`, `geoalchemy2`/`sqlalchemy`, & `psycopg2`

---

## Software Requirements

This codebase requires the following software:

- [`git`](https://git-scm.com/)
- [Python 3](https://docs.conda.io/en/latest/index.html)
- [PostgreSQL](https://www.postgresql.org/) & [PostGIS](https://postgis.net/)

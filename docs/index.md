# :material-map-marker-path: `network-routing`

## About

`network-routing` is a python package to create and analyze routable pedestrian networks, using
both OpenStreetMap data as well as DVRPC's sidewalk data inventory.

The codebase is broken up into three primary modules, each with its own command-line-interface:

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

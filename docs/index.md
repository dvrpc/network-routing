# network-routing

`network-routing` is a python package to create and analyze routable pedestrian networks.

The codebase is broken up into three primary modules, each with its own command-line-interface:

- `db` controls all data I/O
- `access` manages all accessibility/routing analyses
- `gaps` handles all other analysis processes

## Assumptions

You should have the following software installed on your computer:

- miniconda
- PostgreSQL / PostGIS

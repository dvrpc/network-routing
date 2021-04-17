# Sidewalk Gaps

This module builds and analyzes a routable using DVPRC's sidewalk data.

## Command-Line Interface (CLI)

All of the important functionality can be called from a terminal with the top-level command ``sidewalk``

Sensible default values are used across the board, and are defined in the ``.env`` or ``__init__.py`` files.
You can also pass your own parameters directly with the CLI.

### Build the SQL database from DVRPC's source data

Build the analysis database with default settings:

```bash
sidewalk db-setup
```

Build the analysis database with a custom database name and source folder:

```bash
sidewalk db-setup --database my_db_name --folder /my/folder/path/to/shapefiles
```

# :material-weight-lifter: Setup

## Create configuration file

This analysis requires a `.env` file that defines the Postgres database URL and a Google Drive folder path.

You can place this file wherever you intend to run the analysis from. It should look like this:

```
DATABASE_URL=postgresql://username:password@host:5432/database_name
GDRIVE_ROOT=/Volumes/GoogleDrive/My Drive
PG_DUMP_PATH=pg_dump
```

If the `pg_dump` executable in your Python environment does not match the Postgres server version you're running, you'll need to define a full path to the specific version of `pg_dump` that matches your server version. For example, on a Mac with postgres.app installed, you should set `PG_DUMP_PATH` to this:

```
PG_DUMP_PATH=/Applications/Postgres.app/Contents/Versions/latest/bin/pg_dump
```

Make sure that this database exists, and that the PostGIS extension has been enabled. After you've created the database you can enable postgis by running: `CREATE EXTENSION postgis;`

---

## Activate the virtual environment

Although you only need to install and create the `.env` file once, you'll always need to activate the environment before running any commands.

<!-- prettier-ignore -->
=== "conda"
    ```shell
    conda activate network_routing
    ```
=== "venv"
    ```shell
    source ./env/bin/activate
    ```

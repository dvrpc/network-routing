# :material-language-python: Installation & Setup

## Clone the `git` repo and build with local files

Clone the repo, `cd` into the new folder, and build the Python environment with `conda`.

```bash
git clone https://github.com/dvrpc/network-routing.git
cd network-routing
conda env create -f environment.yml
```

After installing the dependencies the `environment.yml` file will install the `network_routing` package via `pip install --editable .` which will allow you to modify the source code locally.

---

## Create the PostGIS database

Using whatever tooling you're most comfortable with, create a PostgreSQL database locally and enable PostGIS within it by running:

```
CREATE EXTENSION postgis;
```

---

## Create configuration file

This analysis requires a file named `.env` that defines the Postgres database URL and a Google Drive folder path.

You can place this file wherever you intend to run the analysis from. It should look like this:

```
DATABASE_URL=postgresql://username:password@host:5432/database_name
GDRIVE_ROOT=/Volumes/GoogleDrive
PG_DUMP_PATH=pg_dump
```

If the `pg_dump` executable in your Python environment does not match the Postgres server version you're running, you'll need to define a full path to the specific version of `pg_dump` that matches your server version. For example, on a Mac with postgres.app installed, you should set `PG_DUMP_PATH` to this:

```
PG_DUMP_PATH=/Applications/Postgres.app/Contents/Versions/latest/bin/pg_dump
```

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

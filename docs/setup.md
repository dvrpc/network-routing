# :material-weight-lifter: Setup

## Create configuration files

Two different configuration files are required for this analysis:

- `.env`
- `database_connections.cfg`

---

### `.env`

The `.env` file contains configuration values including the database name, host, and Google Drive folder path.

You can place this file wherever you intend to run the analysis from. It should look like this:

```
DB_NAME=my_database_name
DB_HOST=localhost
GDRIVE_ROOT=/Volumes/GoogleDrive/My Drive
```

---

### `database_connections.cfg`

The `pg_data_etl` module requires a configuration file that defines basic and superuser credentials for a PostgreSQL database.

If you've used the module before, the file should already exist at:

`/USER HOME/sql_data_io/database_connections.cfg`

If you don't have this file yet, run the following command from a python session within the virtual environment:

```Python
> pg make-config-file
```

The new file will look like the example below. Update usernames, passwords, etc as needed.

```
[DEFAULT]
pw = this-is-a-placeholder-password
port = 5432
super_db = postgres
super_un = postgres
super_pw = there-is-no-password-here

[localhost]
host = localhost
un = postgres
pw = passwordless-setup
```

The title inside square brackets (i.e. `[localhost]`) should match the `DB_HOST` value in the `.env` file.

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

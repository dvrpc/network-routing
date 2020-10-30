# Development Environment

## Create the environment with ``conda`` using the ``env.yml`` file

```bash
(base) $ conda env create -f env.yml
```

Activate the environment:

```bash
(base) $ conda activate network_routing
(network_routing) $
```

## Create a ``.env`` file

This project uses ``python-dotenv`` to configure environment variables.
You'll need to create a file named `.env` in the root project folder. (i.e. `~/github/network_routing`)

It should define the following three variables:
```
DB_NAME=network_routing_analysis
DB_HOST=localhost
GDRIVE_ROOT=/Volumes/GoogleDrive/My Drive
```

On Windows, replace the final line with:
```
GDRIVE_ROOT=G:\My Drive
```

Defining these variables in this way simplifies the database and folder connections all across the project.

## Define SQL database connections

This project utilizes the ``postgis-helpers`` module to facilitate interactions with spatial data within PostgreSQL. Documentation for this  module can be found at https://postgis-helpers.readthedocs.io/en/latest/

The first time this module is imported it will create a configuration file. Every other time it's imported it will read the connection info from this file. 

On a Mac the configuration file can be found at ``/Users/YOURNAME/sql_data_io/database_connections.cfg``

On a Windows machine it can be found at ``C:\Users\YOURNAME\sql_data_io\database_connections.cfg``
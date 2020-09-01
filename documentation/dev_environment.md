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

This project uses ``python-dotenv`` to configure paths to folders.
You don't always need access to these variables, but a few commands
require a pre-configured folder path.

    - ``sidewalk db-setup`` requires ``PROJECT_ROOT``
    - ``sidewalk db-freeze`` requires ``GDRIVE_ROOT``


If you're on Linux\WSL, it might look something like:

```text
PROJECT_ROOT=/mnt/u/folder1/folder2/etc/sidewalk_gap_analysis
```

Windows users might have:
```text
PROJECT_ROOT=U:\folder1\folder2\etc\sidewalk_gap_analysis
GDRIVE_ROOT=G:\My Drive\projects\Sidewalk Gaps
```

And on MacOS:
```text
GDRIVE_ROOT=/Volumes/GoogleDrive/My Drive/projects/Sidewalk Gaps
```

## Define SQL database connections

This project utilizes the ``postgis-helpers`` module to facilitate interactions with spatial data within PostgreSQL. Documentation for this  module can be found at https://postgis-helpers.readthedocs.io/en/latest/

The first time this module is imported it will create a configuration file. Every other time it's imported it will read the connection info from this file. 

On a Mac the configuration file can be found at ``/Users/YOURNAME/sql_data_io/database_connections.cfg``

On a Windows machine it can be found at ``C:\Users\YOURNAME\sql_data_io\database_connections.cfg``
# Setup

## Clone the `git` repo and build the `Python` environment

Clone the repo, `cd` into the new folder, and build the Python environment with `conda`

```bash
git clone https://github.com/dvrpc/network-routing.git
cd network-routing
conda env create -f environment.yml
```

## Create a `.env` file

You can place this file wherever you intend to run the analysis from. It should look like this:

```
DB_NAME=my_database_name
DB_HOST=localhost
GDRIVE_ROOT=/Volumes/GoogleDrive/My Drive
```

## Activate the `conda` environment

Although you only need to install and create the `.env` file once, you'll always need to activate the environment before running any commands.

```bash
conda activate network_routing
```

# :material-remote-desktop: Running this analysis remotely

If you're having trouble with a Windows computer or otherwise don't have the compute power locally necessary for this analysis,
you can run this code in the cloud with following these steps.

## Create a "Droplet" on Digital Ocean

In your Digital Ocean account, create a Virtual Machine ("Droplet") with enough resources to run this analysis. This tutorial
was tested using the following specs:

- 64 GB RAM
- 8 Intel vCPUs
- 160 GB NVME SSD disk
- Ubuntu 20.04 (LTS) x64

Follow [Digital Ocean's initial setup instructions](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-20-04)
to create a non-`root` user with `sudo` permissions.

## Install dependencies

Connect to your droplet and install the following:

### Miniconda

```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### PostgreSQL / PostGIS

```
sudo apt update
sudo apt install postgis
```

### make / tippecanoe

```
sudo apt install make
sudo apt-get install build-essential libsqlite3-dev zlib1g-dev
git clone https://github.com/mapbox/tippecanoe.git
cd tippecanoe
make -j
sudo make install
```

## Prepare for analysis

### Clone the `network-routing` repo from GitHub

```
git clone https://github.com/dvrpc/network-routing.git
```

### Create the `conda` environment

```
cd network-routing
conda env create -f environment.yml
```

### Use Filezilla to upload the necessary shapefiles via FTP

Instead of connecting directly to the shared folder via GoogleDrive, you'll need to copy the necessary
shapefiles via FTP. [Follow these directions to set up the connection](https://medium.com/@Madgeek_in/how-to-connect-digitalocean-droplet-using-sftp-filezilla-2af5e2126ca), and once you're in create the following
folder tree:

```
/home/sammy/GDrive-Mirror/Shared drives/network-routing-repo-data/data
```

and then copy the entire `inputs` folder over.

### Create the PostGIS database

Connect to the root database to create a new one for this analysis:

```
sudo -u postgres psql
```

```
postgres=# CREATE DATABASE example_db;
```

Then connect to the new database and enable PostGIS:

```
sudo -u postgres psql -d example_db
```

```
example_db=# CREATE EXTENSION postgis;
```

### Configure the `.env` file

At the root level of the cloned repo, create a file with the following:

```
DATABASE_URL=postgresql://postgres:your-password@localhost:5432/example_db
GDRIVE_ROOT=/home/sammy/GDrive-Mirror
```

## Run the analysis

At this point you should be set up to run the analysis as normal. If you'd like a familiar interface
to interact with the code files and terminal, install the `Remote-SSH` VSCode plugin and use VSCode
to connect to the droplet and run commands.

At the end of your analysis you'll need to use the FTP to copy the output files from the server back to your local computer.

## Memory errors

If an analysis script is unexpectedly "killed" by the droplet, you may have run out of RAM. If this happens, configure
the droplet's swap usage by following [this tutorial from Digital Ocean](https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-20-04).

You can keep an eye on RAM, swap, CPU, and running processes by logging in to the droplet and running `htop`.

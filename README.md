# network-routing
Python package to create and analyze routable networks

## Development Environment

### Create the environment with ``conda`` using the ``env.yml`` file

```bash
(base) $ conda env create -f env.yml
```

Activate the environment:

```bash
(base) $ conda activate network_routing
(network_routing) $
```

### Create a ``.env`` file

This project uses ``python-dotenv`` to configure paths to folders.
You don't always need access to these variables, but a few commands
require a pre-configured folder path.
    - ``sidewalk download-data`` requires ``PROJECT_ROOT``
    - ``sidewalk load-database`` requires ``GDRIVE_ROOT``


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
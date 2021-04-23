# :material-language-python: Installation

## Option 1: Use `pip` to install into an existing environment

If you already have a python virtual environment, you can install this library with:

```bash
pip install git+https://github.com/dvrpc/network-routing.git
```

## Option 2: Clone the `git` repo and build with local files

Clone the repo, `cd` into the new folder, and build the Python environment with `conda`.

```bash
git clone https://github.com/dvrpc/network-routing.git
cd network-routing
conda env create -f environment.yml
```

After installing the dependencies the `environment.yml` file will install the `network_routing` package via `pip install --editable .` which will allow you to modify the source code locally.

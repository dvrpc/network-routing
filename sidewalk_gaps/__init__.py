"""
``sidewalk_gaps``
-----------------

The PROJECT_ROOT filepath below is only accessible within the DVRPC firewall.

If you're connecting within WSL you'll need to first mount the U: drive:

    $ sudo mkdir /mnt/u
    $ sudo mount -t drvfs U: /mnt/u

"""

import platform
from pathlib import Path

if platform.system() == "Linux":
    PROJECT_ROOT = Path(r"/mnt/u/FY2021/Transportation/TransitBikePed/SidewalkGapAnalysis")

if platform.system() == "Windows":
    PROJECT_ROOT = Path(r"U:\FY2021\Transportation\TransitBikePed\SidewalkGapAnalysis\shapefiles\inputs")


FOLDER_SHP = PROJECT_ROOT / "shapefiles"

FOLDER_SHP_INPUT = FOLDER_SHP / "inputs"

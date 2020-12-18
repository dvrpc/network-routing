import os
from pathlib import Path


def make_vector_tiles(folder: Path, joined_tileset_name: str):
    """Loop through the provided folder path and convert
    each geojson file into its own vector tileset.

    Then merge all tilesets into a single tileset
    with layers for each single tileset.

    The output file will be named:
        folder / joined_tileset_name.mbtiles

    THIS REQUIRES 'tippecanoe' AND WILL NOT WORK IF
    THE COMMAND DOES NOT WORK FROM YOUR TERMINAL.

    On MacOS, install via 'brew install tippecanoe'
    On Windows, you'll need to use WSL. See https://gist.github.com/ryanbaumann/e5c7d76f6eeb8598e66c5785b677726e

    For more info, see: https://github.com/mapbox/tippecanoe
    """

    print("\n\nConverting .geojson files to .mbtiles")
    # Make an individual tileset for each geojson file
    for f in folder.rglob("*.geojson"):
        print(f"\n\nTILING: {f.stem}")
        cmd = f'tippecanoe -o "{folder / f.stem}.mbtiles" -l {f.stem} -f -r1 -pk -pf "{f}"'
        print(cmd, "\n")
        os.system(cmd)

    # Combine all tiles into a single set
    print("\n\nMerging multiple .mbtiles files into a single tilset")
    output_folder = folder / "tileset"

    if not output_folder.exists():
        output_folder.mkdir()

    output_mbtile = output_folder / f"{joined_tileset_name}.mbtiles"

    cmd = f'tile-join -n {joined_tileset_name} -pk -f -o "{output_mbtile}"'
    for f in folder.rglob("*.mbtiles"):
        if joined_tileset_name not in str(f):
            cmd += f' "{f}"'

    print("\n\n", cmd)
    os.system(cmd)

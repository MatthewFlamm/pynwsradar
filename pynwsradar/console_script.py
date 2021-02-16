"""Command-line interface."""
import argparse

from pynwsradar import Nexrad


def create_radar(station, output, layer, num) -> None:
    """Create radar image."""
    radar = Nexrad(station=station)
    radar.update()
    assert radar.layers
    layer = radar.layers[f"{station}_{layer}"]
    layer.update_image(num=num)
    layer.save_image(output)


def main():
    """Make radar imgae with commandline."""
    parser = argparse.ArgumentParser(description="Create NEXRAD qradar image.")
    parser.add_argument("station")
    parser.add_argument("file", help="output file name")
    parser.add_argument("--layer", default="bref_raw")
    parser.add_argument("--num", type=int, default=1, help="number of frames")
    args = parser.parse_args()
    create_radar(args.station, args.file, args.layer, args.num)

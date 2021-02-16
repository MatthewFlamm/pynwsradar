"""Constants for tests."""
from io import BytesIO

import numpy as np
from PIL import Image

STATION = "klwx"
LAYER = "bref_raw"

STATION_URL = f"https://opengeo.ncep.noaa.gov/geoserver/{STATION}/ows"

LEGEND_URLS = [
    "https://opengeo.ncep.noaa.gov:443/geoserver/styles/reflectivity.png",
    "https://opengeo.ncep.noaa.gov:443/geoserver/klwx/ows?service=WMS&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&layer=klwx_bdsa",
]

DEFAULT_SIZE = (800, 800)


def fake_image_bytes(mode="RGBA", size=DEFAULT_SIZE):
    b = BytesIO()
    Image.new(mode, size, tuple(np.random.randint(0, 256, 3))).save(b, "png")
    return b

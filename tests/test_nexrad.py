"""Test NEXRAD."""
from xml.etree import ElementTree

import pytest
import responses
from PIL import Image

from pynwsradar import Nexrad

from .common import basemap_response, legend_response, station_response
from .const import STATION, STATION_URL


def test_nexrad(tmp_path):
    with responses.RequestsMock() as rsps:
        rsps = station_response(rsps)
        rsps = basemap_response(rsps)
        rsps = legend_response(rsps)

        station = Nexrad(STATION)
        station.update()
        assert list(station.layers.keys()) == [
            "klwx_bdhc",
            "klwx_bdsa",
            "klwx_bdzd",
            "klwx_beet",
            "klwx_bohp",
            "klwx_bref_raw",
            "klwx_bsrm",
            "klwx_bstp",
            "klwx_bvel",
            "klwx_bvel_raw",
            "klwx_cref",
            "klwx_hvil",
        ]
        assert station.url == STATION_URL
        assert station.station == STATION
        layer = station.layers["klwx_bref_raw"]

        assert layer.url == STATION_URL
        assert layer.name == "klwx_bref_raw"
        assert (
            layer.abstract
            == "NEXRAD Level 2 Super Resolution Radar Base Reflectivity. This data is provided Multi-Radar-Multi-Sensor (MRMS) algorithm."
        )
        assert layer.crs == ["EPSG:4326", "CRS:84"]
        assert layer.bounding_box == {
            "CRS:84": ("-82.487", "33.976", "-72.487", "43.976"),
            "EPSG:4326": ("33.976", "-82.487", "43.976", "-72.487"),
        }
        layer.update_image()
    file_name = tmp_path / "radar.gif"
    layer.save_image(file_name)
    assert file_name.is_file()

    image_bytes = layer.image()
    assert image_bytes

    with Image.open(file_name) as image:
        assert image.size == (800, 800)
        assert image.n_frames == 1
        assert not image.is_animated


def test_nexrad_new_data():
    with responses.RequestsMock() as rsps:
        rsps = station_response(rsps)

        station = Nexrad(STATION)
        station.update()
    layer1 = station.layers["klwx_bref_raw"]
    assert layer1.dimension
    assert layer1.dimension.dimensions == [
        "2021-02-21T12:07:17.000Z",
        "2021-02-21T12:14:16.000Z",
        "2021-02-21T12:21:11.000Z",
    ]
    assert layer1.dimension.default == "2021-02-21T12:21:11Z"
    with responses.RequestsMock() as rsps:
        rsps = station_response(rsps, file="station_extra_dimension.xml")
        station.update()
    assert station.layers["klwx_bref_raw"] is layer1
    assert layer1.dimension.dimensions == [
        "2021-02-21T12:07:17.000Z",
        "2021-02-21T12:14:16.000Z",
        "2021-02-21T12:21:11.000Z",
        "2021-02-21T12:31:11.000Z",
    ]
    assert layer1.dimension.default == "2021-02-21T12:31:11Z"


def test_nexrad_failed_xmlparse():
    with responses.RequestsMock() as rsps:
        rsps = station_response(rsps, file="station_error.html")

        station = Nexrad(STATION)
        with pytest.raises(ElementTree.ParseError):
            station.update()

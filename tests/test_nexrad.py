"""Test NEXRAD."""
from xml.etree import ElementTree

import pytest
import responses

from pynwsradar import Nexrad

from .common import basemap_response, legend_response, station_response
from .const import STATION, STATION_URL


def test_nexrad():
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
        station.layers["klwx_bref_raw"].update_image()


def test_nexrad_failed_xmlparse():
    with responses.RequestsMock() as rsps:
        rsps = station_response(rsps, file="station_error.html")

        station = Nexrad(STATION)
        with pytest.raises(ElementTree.ParseError):
            station.update()

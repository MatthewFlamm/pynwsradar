"""Fixtures for tests."""
import os
from urllib.parse import parse_qsl

import pytest
import responses

from pynwsradar.const import USGS_NATIONALMAP_URL

from .const import LEGEND_URLS, STATION_URL, fake_image_bytes

LEGEND_BREF_URL = "https://opengeo.ncep.noaa.gov:443/geoserver/styles/reflectivity.png"
LEGEND_BDSA_URL = "https://opengeo.ncep.noaa.gov:443/geoserver/klwx/ows?service=WMS&request=GetLegendGraphic&format=image/png&width=20&height=20&layer=klwx_bdsa"

CAPABILITIES_PARAMS = {"request": "GetCapabilities", "service": "wms"}

BREF_PARAMS = {"request": "GetMap", "service": "wms", "layers": "klwx_bref_raw"}

BDSA_PARAMS = {"request": "GetMap", "service": "wms", "layers": "klwx_bdsa"}


def match_params(params, desired_params):
    for item in desired_params.items():
        if item not in params.items():
            return False
    return True


def station_callback(request):
    # GetCapabilities
    if match_params(request.params, CAPABILITIES_PARAMS):
        with open(
            os.path.join(os.path.dirname(__file__), "data", "station.xml")
        ) as fid:
            data = fid.read()
        return (200, {}, data)

    # bref_raw layer
    elif match_params(request.params, BREF_PARAMS) or match_params(
        request.params, BDSA_PARAMS
    ):
        size = (int(request.params["width"]), int(request.params["height"]))
        return (
            200,
            {},
            fake_image_bytes(size=size).getvalue(),
        )

    raise ConnectionError(f"Could not match params {request.params}")


@pytest.fixture
def responses_nwsradar():
    """Setup responses for nwsradar."""
    with responses.RequestsMock() as rsps:
        with open(
            os.path.join(os.path.dirname(__file__), "data", "station.xml")
        ) as fid:
            body = fid.read()

        rsps.add_callback(
            responses.GET,
            STATION_URL,
            callback=station_callback,
        )

        rsps.add(
            responses.GET,
            USGS_NATIONALMAP_URL,
            body=fake_image_bytes().getvalue(),
            status=200,
        )

        rsps.add(
            responses.GET,
            LEGEND_BREF_URL,
            body=fake_image_bytes(size=(300, 50)).getvalue(),
            status=200,
        )

        yield rsps


@pytest.fixture
def responses_nwsradar_bdsa():
    """Setup responses for nwsradar."""
    with responses.RequestsMock() as rsps:
        with open(
            os.path.join(os.path.dirname(__file__), "data", "station.xml")
        ) as fid:
            body = fid.read()

        rsps.add_callback(
            responses.GET,
            STATION_URL,
            callback=station_callback,
        )

        rsps.add(
            responses.GET,
            USGS_NATIONALMAP_URL,
            body=fake_image_bytes().getvalue(),
            status=200,
        )

        rsps.add(
            responses.GET,
            LEGEND_BDSA_URL,
            body=fake_image_bytes(size=(300, 50)).getvalue(),
            status=200,
        )

        yield rsps

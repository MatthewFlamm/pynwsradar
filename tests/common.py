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


def get_station_callback(capabilities_file="station.xml"):
    def station_callback(request):
        # GetCapabilities
        if match_params(request.params, CAPABILITIES_PARAMS):
            with open(
                os.path.join(os.path.dirname(__file__), "data", capabilities_file)
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

    return station_callback


def station_response(rsps, file="station.xml"):
    rsps.add_callback(
        responses.GET,
        STATION_URL,
        callback=get_station_callback(file),
    )
    return rsps


def basemap_response(rsps):
    rsps.add(
        responses.GET,
        USGS_NATIONALMAP_URL,
        body=fake_image_bytes().getvalue(),
        status=200,
    )
    return rsps


def legend_response(rsps, legend_url=LEGEND_BREF_URL):
    rsps.add(
        responses.GET,
        legend_url,
        body=fake_image_bytes(size=(300, 50)).getvalue(),
        status=200,
    )

    return rsps

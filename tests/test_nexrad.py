"""Test NEXRAD."""
from pynwsradar import Nexrad

from .const import STATION, STATION_URL


def test_nexrad(responses_nwsradar):
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

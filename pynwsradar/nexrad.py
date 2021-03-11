"""NEXRAD radar."""
import logging
from io import BytesIO
from typing import IO, Dict, List, Optional, Tuple
from xml.etree import ElementTree

import numpy as np
import requests
from PIL import Image

from .const import NAMESPACE_WMS, NAMESPACE_XLINK, USGS_NATIONALMAP_URL

_LOGGER = logging.getLogger(__name__)

# pylint: disable=C0301
# from https://stackoverflow.com/questions/765736/how-to--use-pil-to-make-all-white-pixels-transparent


def white_to_transparent(img):
    """Make all white pixels transparent."""
    num_img = np.asarray(img.convert("RGBA")).copy()
    num_img[:, :, 3] = (255 * (num_img[:, :, :3] != 255).any(axis=2)).astype(np.uint8)
    return Image.fromarray(num_img)


def national_map_image(bbox: str, size: Tuple[int, int]) -> Image:
    """Return national map image."""
    params = {
        "version": "1.3.0",
        "request": "GetMap",
        "service": "wms",
        "layers": "0",
        "styles": "default",
        "CRS": "CRS:84",
        "format": "image/png",
        "width": str(size[0]),
        "height": str(size[1]),
        "bbox": bbox,
    }

    response = requests.get(
        USGS_NATIONALMAP_URL,
        params=params,
    )
    return Image.open(BytesIO(response.content))


class Dimension:
    """Time dimension."""

    def __init__(self, dimension: ElementTree.Element):
        """Initialize time dimension."""
        self._dimension = dimension

        default = dimension.get("default")
        assert default
        self._default = default

        dimensions_text = dimension.text
        assert dimensions_text
        dimensions = dimensions_text.split(",")
        assert all(dimensions)
        self._dimensions = dimensions

    @property
    def default(self) -> str:
        """Default time."""
        return self._default

    @property
    def dimensions(self) -> List[str]:
        """All available times."""
        return self._dimensions


class Layer:
    """A layer."""

    def __init__(self, station: str, layer: ElementTree.Element, nexrad: "Nexrad"):
        """Initialize a layer."""
        self._station = station
        self._layer = layer
        self._nexrad = nexrad

        self._set_name(layer)
        self._set_abstract(layer)
        self._set_crs(layer)
        self._set_bounding_box(layer)

        dimension_element = layer.find(f"{NAMESPACE_WMS}Dimension")
        assert dimension_element is not None
        self._dimension = Dimension(dimension_element)

        legend_element = layer.find(
            f"{NAMESPACE_WMS}Style/{NAMESPACE_WMS}LegendURL/{NAMESPACE_WMS}OnlineResource"
        )
        assert legend_element is not None
        legend_url = legend_element.get(f"{NAMESPACE_XLINK}href")
        assert legend_url is not None
        self._legend_url = legend_url

        self._legend: Optional[Image] = None
        self._basemap: Optional[Image] = None
        self._images: Dict[str, Image] = {}
        self._frames: Dict[str, Image] = {}

    def _set_name(self, layer: ElementTree.Element):
        """Validate and set name."""
        name_element = layer.find(f"{NAMESPACE_WMS}Name")
        if name_element is None or not hasattr(name_element, "text"):
            raise ValueError("Name must be present.")

        name = name_element.text
        assert name
        self._name = name

    def _set_abstract(self, layer: ElementTree.Element):
        """Validate and set abstract."""
        abstract_element = layer.find(f"{NAMESPACE_WMS}Abstract")
        if abstract_element is None or not hasattr(abstract_element, "text"):
            raise ValueError("Abstract must be present.")
        self._abstract = abstract_element.text

    def _set_crs(self, layer: ElementTree.Element):
        """Validate and set CRS."""
        crs_elements = layer.findall(f"{NAMESPACE_WMS}CRS")
        crs: List[str] = []
        for crs_element in crs_elements:
            if crs_element is None or not hasattr(crs_element, "text"):
                continue
            crs_text = crs_element.text
            assert crs_text
            crs.append(crs_text)
        self._crs = crs

    def _set_bounding_box(self, layer: ElementTree.Element):
        """Validate and set CRS."""
        bounding_box_element = layer.findall(f"{NAMESPACE_WMS}BoundingBox")
        if bounding_box_element is None:
            raise ValueError("Bounding box must be present.")
        bounding_box: Dict[str, Tuple[str, str, str, str]] = dict()
        for b in bounding_box_element:
            CRS = b.get("CRS")
            minx = b.get("minx")
            miny = b.get("miny")
            maxx = b.get("maxx")
            maxy = b.get("maxy")
            assert CRS
            assert minx
            assert miny
            assert maxx
            assert maxy

            bounding_box[CRS] = (minx, miny, maxx, maxy)
        self._bounding_box = bounding_box

    def update_dimension(self, new_layer: "Layer") -> None:
        """Update time dimension with new data."""
        self._dimension = new_layer.dimension

    @property
    def url(self) -> str:
        """Url for station."""
        return f"https://opengeo.ncep.noaa.gov/geoserver/{self._station}/ows"

    @property
    def name(self) -> str:
        """Name of layer."""
        return self._name

    @property
    def abstract(self) -> Optional[str]:
        """Abstract of a layer."""
        return self._abstract

    @property
    def crs(self) -> List[str]:
        """CRS of a layer."""
        return self._crs

    @property
    def bounding_box(self) -> Dict[str, Tuple[str, str, str, str]]:
        """Bounding box of layer."""
        return self._bounding_box

    @property
    def dimension(self) -> Dimension:
        """Time dimension of a layer."""
        return self._dimension

    def update_legend(self, width: int) -> None:
        """Update legend and size to width."""
        response = requests.get(self._legend_url)
        response.raise_for_status()
        legend_image = Image.open(BytesIO(response.content))
        new_height = int(legend_image.height * width / legend_image.width)
        self._legend = legend_image.resize((width, new_height))

    def update_basemap(self, size: Tuple[int, int]) -> None:
        """Update basemap with size."""
        self._basemap = national_map_image(
            ",".join(self.bounding_box["CRS:84"]), size
        ).convert("RGBA")

    def update_image(
        self,
        num: int = 1,
        size: Tuple[int, int] = (800, 800),
        nexrad_update: bool = False,
    ) -> None:
        """Update image with num latest frames, size, and optional update dimensions."""
        if nexrad_update:
            self._nexrad.update()

        if self._basemap is None:
            self.update_basemap(size)
        elif not self._basemap.size == size:
            self.update_basemap(size)

        if self._legend is None:
            self.update_legend(size[0])
        elif not self._legend.width == size[0]:
            self.update_legend(size[0])

        for key in self._images:
            if key not in self.dimension.dimensions[-num:]:
                self._images.pop(key)

        for dimension in self.dimension.dimensions[-num:]:
            if dimension in self._images:
                continue

            params = {
                "version": "1.3.0",
                "request": "GetMap",
                "service": "wms",
                "layers": self.name,
                "CRS": "CRS:84",
                "format": "image/png",
                "width": str(size[0]),
                "height": str(size[1]),
                "bbox": ",".join(self.bounding_box["CRS:84"]),
                "time": dimension,
            }

            response = requests.get(
                self.url,
                params=params,
            )
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            self._images[dimension] = white_to_transparent(image)

    def _gen_frames(self) -> None:
        """Generate frames from images."""
        for key in self._frames:
            if key not in self._images:
                self._frames.pop(key)
        for key in self._images:
            if key not in self._frames:
                self._frames[key] = self._combine_images(self._images[key])

    def _combine_images(self, image: Image) -> Image:
        """Combine provided image with basemap and overlays."""
        assert self._basemap
        image1 = Image.alpha_composite(self._basemap, image)
        assert self._legend
        image1.paste(self._legend, (0, image1.height - self._legend.height))
        return image1

    def image(self) -> bytes:
        """Return BytesIO object if no filename, or save to file."""
        bytes_obj = BytesIO()
        self._gen_frames()
        frames = list(self._frames.values())
        if frames:
            frames[0].save(
                bytes_obj,
                format="gif",
                save_all=True,
                append_images=frames[1:],
                loop=0,
                duration=500,
            )
        else:
            raise ValueError
        return bytes_obj.getvalue()

    def save_image(self, filename: IO) -> None:
        """Save to file."""
        self._gen_frames()
        frames = list(self._frames.values())
        if frames:
            frames[0].save(
                filename,
                format="gif",
                save_all=True,
                append_images=frames[1:],
                loop=0,
                duration=500,
            )
        else:
            raise ValueError


class Nexrad:
    """Main NEXRAD class."""

    def __init__(self, station: str):
        """Initialize NEXRAD station."""
        self._station: str = station
        self._layer_list: Optional[List[Layer]] = None
        self._layer_dict: Optional[Dict[str, Layer]] = None
        self._data: Optional[ElementTree.Element] = None

    def update(self) -> None:
        """Update capabilities."""
        response = requests.get(
            self.url,
            params={
                "version": "1.3.0",
                "request": "GetCapabilities",
                "service": "wms",
            },
        )
        raw_data = response.content
        try:
            self._data = ElementTree.fromstring(raw_data)
        except ElementTree.ParseError as err:
            _LOGGER.error("url: %s\nraw_data: %s", self.url, raw_data)
            raise err
        layers = self._data.findall(
            f".//{NAMESPACE_WMS}Capability/{NAMESPACE_WMS}Layer/{NAMESPACE_WMS}Layer"
        )
        layer_list = [Layer(self.station, layer, self) for layer in layers]
        layer_dict = {layer.name: layer for layer in layer_list}
        if self._layer_dict is None:
            self._layer_list = layer_list
            self._layer_dict = layer_dict
        else:
            for layer in self._layer_dict:
                self._layer_dict[layer].update_dimension(layer_dict[layer])

    @property
    def station(self) -> str:
        """Station."""
        return self._station

    @property
    def url(self) -> str:
        """Url for station."""
        return f"https://opengeo.ncep.noaa.gov/geoserver/{self.station}/ows"

    @property
    def layers(self) -> Optional[Dict[str, Layer]]:
        """Layer objects."""
        return self._layer_dict

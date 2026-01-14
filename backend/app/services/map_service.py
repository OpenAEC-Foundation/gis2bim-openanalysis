"""
Map Service - Fetch map images from WMS/WMTS services
"""
import httpx
from typing import List, Optional, Dict
from io import BytesIO
from PIL import Image
import asyncio
import math


class MapService:
    """Service for fetching map images from geodata services"""

    # Layer configurations - Updated January 2026
    # All WMS services need STYLES= parameter
    LAYERS: Dict[str, dict] = {
        # === BASISKAARTEN ===
        "top10nl": {
            "type": "WMS",
            "url": "https://service.pdok.nl/brt/top10nl/wms/v1_0",
            "layer": "top10nl",
        },
        "openstreetmap": {
            "type": "TILE",
            "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "layer": "osm",
        },

        # === KADASTER & BAG ===
        "kadastrale-kaart": {
            "type": "WMS",
            "url": "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0",
            "layer": "Perceel",
        },
        "bag-panden": {
            "type": "WMS",
            "url": "https://service.pdok.nl/lv/bag/wms/v2_0",
            "layer": "pand",
        },
        # BGT requires authorization - use TOP10NL gebouw instead
        "bgt-gebouwen": {
            "type": "WMS",
            "url": "https://service.pdok.nl/brt/top10nl/wms/v1_0",
            "layer": "gebouw",
        },

        # === LUCHTFOTO'S ===
        "luchtfoto-actueel": {
            "type": "WMS",
            "url": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
            "layer": "Actueel_orthoHR",
        },
        "luchtfoto-2023": {
            "type": "WMS",
            "url": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
            "layer": "2023_orthoHR",
        },
        "luchtfoto-2022": {
            "type": "WMS",
            "url": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
            "layer": "2022_orthoHR",
        },

        # === HOOGTE (AHN) ===
        "ahn-dsm": {
            "type": "WMS",
            "url": "https://service.pdok.nl/rws/ahn/wms/v1_0",
            "layer": "dsm_05m",
        },
        "ahn-dtm": {
            "type": "WMS",
            "url": "https://service.pdok.nl/rws/ahn/wms/v1_0",
            "layer": "dtm_05m",
        },

        # === RUIMTELIJKE PLANNEN ===
        "bestemmingsplan": {
            "type": "WMS",
            "url": "https://service.pdok.nl/kadaster/plu/wms/v1_0",
            "layer": "enkelbestemming",
        },
        "dubbelbestemming": {
            "type": "WMS",
            "url": "https://service.pdok.nl/kadaster/plu/wms/v1_0",
            "layer": "dubbelbestemming",
        },
        "bouwvlak": {
            "type": "WMS",
            "url": "https://service.pdok.nl/kadaster/plu/wms/v1_0",
            "layer": "bouwvlak",
        },

        # === BODEM ===
        "bodemkaart": {
            "type": "WMS",
            "url": "https://service.pdok.nl/bzk/bro-bodemkaart/wms/v1_0",
            "layer": "soilarea",
        },

        # === BESTUURLIJKE GRENZEN ===
        "gemeentegrenzen": {
            "type": "WMS",
            "url": "https://service.pdok.nl/kadaster/bestuurlijkegebieden/wms/v1_0",
            "layer": "Gemeentegebied",
        },
        "provinciegrenzen": {
            "type": "WMS",
            "url": "https://service.pdok.nl/kadaster/bestuurlijkegebieden/wms/v1_0",
            "layer": "Provinciegebied",
        },

        # === NATUUR ===
        "natura2000": {
            "type": "WMS",
            "url": "https://service.pdok.nl/rvo/natura2000/wms/v1_0",
            "layer": "natura2000",
        },

        # === CULTUURHISTORIE (use TOP10NL as fallback) ===
        "rijksmonumenten": {
            "type": "WMS",
            "url": "https://service.pdok.nl/brt/top10nl/wms/v1_0",
            "layer": "gebouw",
        },
    }

    def __init__(self):
        self.client = None

    async def _get_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=60.0)
        return self.client

    def calculate_bbox(
        self,
        lat: float,
        lng: float,
        scale: int,
        paper_size: str = "A3",
        orientation: str = "landscape"
    ) -> tuple:
        """
        Calculate bounding box based on center point and scale
        Returns (min_x, min_y, max_x, max_y) in EPSG:28992 (RD)
        """
        # A3 dimensions in mm
        if paper_size == "A3":
            paper_w_mm = 420 if orientation == "landscape" else 297
            paper_h_mm = 297 if orientation == "landscape" else 420
        else:  # A4
            paper_w_mm = 297 if orientation == "landscape" else 210
            paper_h_mm = 210 if orientation == "landscape" else 297

        # Map extent in meters
        extent_w = (paper_w_mm / 1000) * scale
        extent_h = (paper_h_mm / 1000) * scale

        # Convert WGS84 to approximate RD coordinates
        # This is a simplified conversion - for production use pyproj
        rd_x, rd_y = self.wgs84_to_rd(lat, lng)

        min_x = rd_x - extent_w / 2
        max_x = rd_x + extent_w / 2
        min_y = rd_y - extent_h / 2
        max_y = rd_y + extent_h / 2

        return (min_x, min_y, max_x, max_y)

    def wgs84_to_rd(self, lat: float, lng: float) -> tuple:
        """
        Convert WGS84 coordinates to RD (EPSG:28992)
        Simplified conversion for Netherlands
        """
        # Reference point (Amersfoort)
        ref_lat = 52.15517
        ref_lng = 5.38720
        ref_x = 155000
        ref_y = 463000

        # Simplified conversion factors
        dlat = lat - ref_lat
        dlng = lng - ref_lng

        x = ref_x + dlng * 111320 * math.cos(math.radians(ref_lat))
        y = ref_y + dlat * 110540

        return (x, y)

    async def get_map_image(
        self,
        layer_id: str,
        lat: float,
        lng: float,
        scale: int = 2500,
        overlay_layers: List[str] = None,
        width: int = 1600,
        height: int = 1131,
        paper_size: str = "A3",
        orientation: str = "landscape"
    ) -> Optional[bytes]:
        """
        Fetch a map image for the specified layer and location
        """
        print(f"[MapService] Fetching layer: {layer_id} at ({lat}, {lng}) scale={scale}")

        if layer_id == "samenvatting":
            # Return None for summary page - will be generated differently
            print(f"[MapService] Skipping summary page")
            return None

        layer_config = self.LAYERS.get(layer_id)
        if not layer_config:
            # Return placeholder for unknown layers
            print(f"[MapService] ERROR: Unknown layer_id: {layer_id}")
            print(f"[MapService] Available layers: {list(self.LAYERS.keys())}")
            return None

        # Calculate bounding box
        bbox = self.calculate_bbox(lat, lng, scale, paper_size, orientation)

        # Fetch base layer
        base_image = await self._fetch_wms_image(layer_config, bbox, width, height)

        if base_image and overlay_layers:
            # Composite overlay layers
            base_pil = Image.open(BytesIO(base_image)).convert("RGBA")

            for overlay_id in overlay_layers:
                overlay_config = self.LAYERS.get(overlay_id)
                if overlay_config:
                    overlay_bytes = await self._fetch_wms_image(overlay_config, bbox, width, height)
                    if overlay_bytes:
                        overlay_pil = Image.open(BytesIO(overlay_bytes)).convert("RGBA")
                        base_pil = Image.alpha_composite(base_pil, overlay_pil)

            # Convert back to bytes
            output = BytesIO()
            base_pil.save(output, format="PNG")
            return output.getvalue()

        return base_image

    async def _fetch_wms_image(
        self,
        layer_config: dict,
        bbox: tuple,
        width: int,
        height: int
    ) -> Optional[bytes]:
        """Fetch a single WMS image"""
        client = await self._get_client()
        print(f"[MapService] Fetching WMS: {layer_config.get('layer')} from {layer_config.get('url')}")

        if layer_config["type"] == "WMS":
            params = {
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer_config["layer"],
                "CRS": "EPSG:28992",
                "BBOX": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                "WIDTH": width,
                "HEIGHT": height,
                "FORMAT": "image/png",
                "TRANSPARENT": "true",
                "STYLES": ""  # Required by many WMS servers
            }

            try:
                response = await client.get(layer_config["url"], params=params)
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type:
                        print(f"[MapService] SUCCESS: {layer_config['layer']} - {len(response.content)} bytes")
                        return response.content
                    else:
                        print(f"[MapService] ERROR: WMS returned non-image: {content_type} for {layer_config['layer']}")
                        print(f"[MapService] Response body: {response.text[:500]}")
                else:
                    print(f"[MapService] ERROR: WMS error {response.status_code} for {layer_config['layer']}: {response.text[:200]}")
            except Exception as e:
                print(f"[MapService] EXCEPTION: Error fetching WMS layer {layer_config.get('layer', 'unknown')}: {type(e).__name__}: {e}")
                return None

        elif layer_config["type"] == "WMTS":
            # WMTS with correct RD tile calculation (based on GIS2BIM)
            return await self._fetch_wmts_tiles(layer_config, bbox, width, height)

        return None

    async def _fetch_wmts_tiles(
        self,
        layer_config: dict,
        bbox: tuple,
        width: int,
        height: int
    ) -> Optional[bytes]:
        """
        Fetch WMTS tiles for RD coordinate system (EPSG:28992)
        Based on GIS2BIM implementation with correct tile matrix origin
        """
        client = await self._get_client()

        # WMTS tile matrix parameters for EPSG:28992 (RD)
        # Origin point of the tile matrix
        xcorner = -285401.92
        ycorner = 903402.0
        pixel_width = 256

        # Zoom level resolutions (meters per pixel)
        zoomleveldata = {
            0: 3440.640,
            1: 1720.320,
            2: 860.160,
            3: 430.080,
            4: 215.040,
            5: 107.520,
            6: 53.760,
            7: 26.880,
            8: 13.440,
            9: 6.720,
            10: 3.360,
            11: 1.680,
            12: 0.840,
            13: 0.420,
            14: 0.210,
            15: 0.105,
            16: 0.0525
        }

        # Calculate center of bbox
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        bbox_width = bbox[2] - bbox[0]

        # Determine zoom level based on desired resolution
        target_resolution = bbox_width / width
        zoom_level = 10  # Default
        for level, resolution in sorted(zoomleveldata.items()):
            if resolution <= target_resolution:
                zoom_level = level
                break

        resolution = zoomleveldata.get(zoom_level, 3.360)
        tile_size_m = pixel_width * resolution

        # Calculate tile coordinates
        tile_x = int((center_x - xcorner) / tile_size_m)
        tile_y = int((ycorner - center_y) / tile_size_m)

        # Calculate how many tiles we need to cover the bbox
        tiles_needed_x = math.ceil(bbox_width / tile_size_m) + 2
        tiles_needed_y = math.ceil((bbox[3] - bbox[1]) / tile_size_m) + 2

        # Calculate tile range
        start_tile_x = tile_x - tiles_needed_x // 2
        start_tile_y = tile_y - tiles_needed_y // 2
        end_tile_x = start_tile_x + tiles_needed_x
        end_tile_y = start_tile_y + tiles_needed_y

        # Fetch and stitch tiles
        try:
            from PIL import Image
            from io import BytesIO

            # Create composite image
            total_width = tiles_needed_x * pixel_width
            total_height = tiles_needed_y * pixel_width
            composite = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 0))

            base_url = layer_config["url"]
            layer_name = layer_config["layer"]

            for ty_idx, ty in enumerate(range(start_tile_y, end_tile_y)):
                for tx_idx, tx in enumerate(range(start_tile_x, end_tile_x)):
                    # Build WMTS GetTile URL
                    tile_url = (
                        f"{base_url}?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
                        f"&LAYER={layer_name}"
                        f"&STYLE=default"
                        f"&TILEMATRIXSET=EPSG:28992"
                        f"&TILEMATRIX=EPSG:28992:{zoom_level}"
                        f"&TILEROW={ty}"
                        f"&TILECOL={tx}"
                        f"&FORMAT=image/png"
                    )

                    try:
                        response = await client.get(tile_url)
                        if response.status_code == 200 and "image" in response.headers.get("content-type", ""):
                            tile_img = Image.open(BytesIO(response.content)).convert('RGBA')
                            composite.paste(tile_img, (tx_idx * pixel_width, ty_idx * pixel_width))
                    except Exception as e:
                        print(f"[WMTS] Error fetching tile ({tx}, {ty}): {e}")

            # Calculate the bbox of the fetched tiles
            tiles_min_x = xcorner + start_tile_x * tile_size_m
            tiles_max_y = ycorner - start_tile_y * tile_size_m
            tiles_max_x = tiles_min_x + tiles_needed_x * tile_size_m
            tiles_min_y = tiles_max_y - tiles_needed_y * tile_size_m

            # Calculate crop coordinates
            pixels_per_meter = pixel_width / tile_size_m
            crop_left = int((bbox[0] - tiles_min_x) * pixels_per_meter)
            crop_top = int((tiles_max_y - bbox[3]) * pixels_per_meter)
            crop_right = int((bbox[2] - tiles_min_x) * pixels_per_meter)
            crop_bottom = int((tiles_max_y - bbox[1]) * pixels_per_meter)

            # Ensure crop coordinates are within bounds
            crop_left = max(0, crop_left)
            crop_top = max(0, crop_top)
            crop_right = min(total_width, crop_right)
            crop_bottom = min(total_height, crop_bottom)

            # Crop and resize to requested dimensions
            cropped = composite.crop((crop_left, crop_top, crop_right, crop_bottom))
            final = cropped.resize((width, height), Image.Resampling.LANCZOS)

            # Convert to bytes
            output = BytesIO()
            final.save(output, format='PNG')
            print(f"[WMTS] SUCCESS: Stitched {tiles_needed_x}x{tiles_needed_y} tiles for {layer_name}")
            return output.getvalue()

        except Exception as e:
            print(f"[WMTS] Error stitching tiles: {e}")
            return None

    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None

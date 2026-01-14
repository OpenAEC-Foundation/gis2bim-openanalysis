"""
DXF Generator - Create DXF files from cadastral (Kadaster) data
"""
import ezdxf
from ezdxf import units
from io import BytesIO
import httpx
from typing import Optional, Dict, List, Tuple
import json


class DXFGenerator:
    """Generate DXF files from WFS cadastral data"""

    # PDOK Kadaster WFS endpoint
    KADASTER_WFS_URL = "https://service.pdok.nl/kadaster/kadastralekaart/wfs/v5_0"

    # Layer colors (AutoCAD color indices)
    COLORS = {
        "perceel": 3,        # Green
        "bebouwing": 1,      # Red
        "pand": 1,           # Red
        "openbareruimte": 5, # Blue
        "default": 7         # White
    }

    def __init__(self):
        self.doc = ezdxf.new('R2010')  # AutoCAD 2010 format for compatibility
        self.doc.units = units.M  # Meters
        self.msp = self.doc.modelspace()

        # Create layers
        self._create_layers()

    def _create_layers(self):
        """Create DXF layers for different feature types"""
        layers = [
            ("Perceel", 3),           # Green
            ("Bebouwing", 1),         # Red
            ("OpenbareRuimteNaam", 5), # Blue
            ("Annotatie", 7),         # White
        ]

        for name, color in layers:
            self.doc.layers.add(name, color=color)

    async def fetch_cadastral_data(
        self,
        bbox: Tuple[float, float, float, float],
        layers: List[str] = None
    ) -> Dict:
        """
        Fetch cadastral data from PDOK Kadaster WFS

        Args:
            bbox: Bounding box in RD coordinates (minx, miny, maxx, maxy)
            layers: List of layer names to fetch (default: Perceel, Bebouwing)

        Returns:
            Dictionary with GeoJSON features per layer
        """
        if layers is None:
            layers = ["Perceel", "OpenbareRuimteNaam"]

        results = {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for layer_name in layers:
                try:
                    # WFS GetFeature request
                    params = {
                        "service": "WFS",
                        "version": "2.0.0",
                        "request": "GetFeature",
                        "typeName": f"kadastralekaart:{layer_name}",
                        "outputFormat": "application/json",
                        "srsName": "EPSG:28992",
                        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:28992"
                    }

                    response = await client.get(self.KADASTER_WFS_URL, params=params)

                    if response.status_code == 200:
                        data = response.json()
                        results[layer_name] = data.get("features", [])
                        print(f"[DXF] Fetched {len(results[layer_name])} features from {layer_name}")
                    else:
                        print(f"[DXF] Error fetching {layer_name}: {response.status_code}")
                        results[layer_name] = []

                except Exception as e:
                    print(f"[DXF] Exception fetching {layer_name}: {e}")
                    results[layer_name] = []

        return results

    def add_features_to_dxf(self, features: Dict):
        """Add GeoJSON features to DXF document"""
        for layer_name, feature_list in features.items():
            dxf_layer = layer_name if layer_name in ["Perceel", "Bebouwing", "OpenbareRuimteNaam"] else "Perceel"

            for feature in feature_list:
                geometry = feature.get("geometry", {})
                properties = feature.get("properties", {})

                geom_type = geometry.get("type", "")
                coords = geometry.get("coordinates", [])

                if geom_type == "Polygon":
                    self._add_polygon(coords, dxf_layer, properties)
                elif geom_type == "MultiPolygon":
                    for polygon_coords in coords:
                        self._add_polygon(polygon_coords, dxf_layer, properties)
                elif geom_type == "LineString":
                    self._add_line(coords, dxf_layer)
                elif geom_type == "Point":
                    self._add_point(coords, dxf_layer, properties)

    def _add_polygon(self, coords: List, layer: str, properties: Dict):
        """Add a polygon to the DXF"""
        if not coords or len(coords) == 0:
            return

        # Outer ring
        outer_ring = coords[0]
        if len(outer_ring) >= 3:
            points = [(p[0], p[1]) for p in outer_ring]
            self.msp.add_lwpolyline(points, close=True, dxfattribs={"layer": layer})

        # Inner rings (holes)
        for inner_ring in coords[1:]:
            if len(inner_ring) >= 3:
                points = [(p[0], p[1]) for p in inner_ring]
                self.msp.add_lwpolyline(points, close=True, dxfattribs={"layer": layer})

        # Add label if available
        label = properties.get("kadastraleAanduiding") or properties.get("tekst") or properties.get("naam")
        if label and len(outer_ring) >= 3:
            # Calculate centroid for label placement
            centroid = self._calculate_centroid(outer_ring)
            self.msp.add_text(
                str(label),
                dxfattribs={
                    "layer": "Annotatie",
                    "height": 2.0,
                    "insert": centroid
                }
            )

    def _add_line(self, coords: List, layer: str):
        """Add a line to the DXF"""
        if len(coords) >= 2:
            points = [(p[0], p[1]) for p in coords]
            self.msp.add_lwpolyline(points, dxfattribs={"layer": layer})

    def _add_point(self, coords: List, layer: str, properties: Dict):
        """Add a point/text to the DXF"""
        if len(coords) >= 2:
            label = properties.get("tekst") or properties.get("naam") or ""
            if label:
                self.msp.add_text(
                    str(label),
                    dxfattribs={
                        "layer": layer,
                        "height": 2.0,
                        "insert": (coords[0], coords[1])
                    }
                )
            else:
                self.msp.add_point((coords[0], coords[1]), dxfattribs={"layer": layer})

    def _calculate_centroid(self, coords: List) -> Tuple[float, float]:
        """Calculate centroid of a polygon"""
        if not coords:
            return (0, 0)

        x_sum = sum(p[0] for p in coords)
        y_sum = sum(p[1] for p in coords)
        n = len(coords)

        return (x_sum / n, y_sum / n)

    def get_bytes(self) -> bytes:
        """Get DXF as bytes"""
        from io import StringIO
        import tempfile
        import os

        # ezdxf needs to write to a file or StringIO
        # Write to a temp file and read back as bytes
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.doc.saveas(tmp_path)
            with open(tmp_path, 'rb') as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def save(self, filepath: str):
        """Save DXF to file"""
        self.doc.saveas(filepath)


async def generate_cadastral_dxf(
    lat: float,
    lng: float,
    radius: float = 250,
    layers: List[str] = None
) -> bytes:
    """
    Generate a DXF file with cadastral data around a location

    Args:
        lat: Latitude (WGS84)
        lng: Longitude (WGS84)
        radius: Radius in meters (half of bounding box width)
        layers: WFS layers to include

    Returns:
        DXF file as bytes
    """
    # Convert WGS84 to RD (Rijksdriehoek) coordinates
    from app.services.map_service import MapService
    map_service = MapService()
    rd_x, rd_y = map_service.wgs84_to_rd(lat, lng)

    # Calculate bounding box
    bbox = (
        rd_x - radius,
        rd_y - radius,
        rd_x + radius,
        rd_y + radius
    )

    print(f"[DXF] Generating DXF for bbox: {bbox}")

    # Create DXF generator
    generator = DXFGenerator()

    # Fetch cadastral data
    features = await generator.fetch_cadastral_data(bbox, layers)

    # Add features to DXF
    generator.add_features_to_dxf(features)

    # Return DXF bytes
    return generator.get_bytes()

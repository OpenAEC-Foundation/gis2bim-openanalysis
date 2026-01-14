"""
Layers API - Manage available geodata layers
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import httpx
from io import BytesIO

router = APIRouter()


class LayerConfig(BaseModel):
    """Layer configuration"""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    source: str
    type: str  # WMS, WMTS
    url: str
    layer: str
    color: Optional[str] = "#666666"
    default: bool = False


class BoundingBox(BaseModel):
    """Bounding box in WGS84"""
    min_lat: float
    min_lng: float
    max_lat: float
    max_lng: float


# Available layers configuration
AVAILABLE_LAYERS: List[LayerConfig] = [
    LayerConfig(
        id="top10nl",
        name="TOP10NL Topografische Kaart",
        description="Topografische basiskaart van Nederland 1:10.000",
        category="topografie",
        source="PDOK",
        type="WMTS",
        url="https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0",
        layer="standaard",
        color="#10b981",
        default=True
    ),
    LayerConfig(
        id="kadastrale-kaart",
        name="Kadastrale Kaart",
        description="Kadastrale percelen en grenzen",
        category="kadaster",
        source="PDOK",
        type="WMS",
        url="https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0",
        layer="Perceel",
        color="#dc2626",
        default=True
    ),
    LayerConfig(
        id="bag-panden",
        name="BAG Panden",
        description="Basisregistratie Adressen en Gebouwen",
        category="kadaster",
        source="PDOK",
        type="WMS",
        url="https://service.pdok.nl/lv/bag/wms/v2_0",
        layer="pand",
        color="#ef4444",
        default=True
    ),
    LayerConfig(
        id="bgt",
        name="BGT Grootschalige Topografie",
        description="Basisregistratie Grootschalige Topografie",
        category="topografie",
        source="PDOK",
        type="WMS",
        url="https://service.pdok.nl/lv/bgt/wms/v1_0",
        layer="bgt_begroeidterreindeel",
        color="#22c55e",
        default=True
    ),
    LayerConfig(
        id="luchtfoto-actueel",
        name="Luchtfoto Actueel",
        description="Meest recente luchtfoto's",
        category="luchtfoto",
        source="PDOK",
        type="WMTS",
        url="https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0",
        layer="Actueel_orthoHR",
        color="#0ea5e9",
        default=True
    ),
    LayerConfig(
        id="ahn3-dsm",
        name="AHN3 Hoogtekaart",
        description="Actueel Hoogtebestand Nederland DSM",
        category="topografie",
        source="PDOK",
        type="WMS",
        url="https://service.pdok.nl/rws/ahn/wms/v1_0",
        layer="dsm_05m",
        color="#8b5cf6",
        default=True
    ),
    LayerConfig(
        id="bestemmingsplan",
        name="Bestemmingsplannen",
        description="Geldende bestemmingsplannen",
        category="thematisch",
        source="Ruimtelijkeplannen.nl",
        type="WMS",
        url="https://service.pdok.nl/pbl/ruimtelijkeplannen/wms/v1_0",
        layer="bestemmingsplangebied",
        color="#f97316",
        default=True
    ),
    LayerConfig(
        id="natura2000",
        name="Natura 2000",
        description="Europese beschermde natuurgebieden",
        category="milieu",
        source="PDOK",
        type="WMS",
        url="https://service.pdok.nl/rvo/natura2000/wms/v1_0",
        layer="natura2000",
        color="#16a34a",
        default=True
    ),
]


@router.get("/", response_model=List[LayerConfig])
async def get_layers():
    """Get all available layers"""
    return AVAILABLE_LAYERS


@router.get("/categories")
async def get_categories():
    """Get all unique categories"""
    categories = list(set(layer.category for layer in AVAILABLE_LAYERS))
    return sorted(categories)


@router.get("/{layer_id}", response_model=LayerConfig)
async def get_layer(layer_id: str):
    """Get a specific layer by ID"""
    for layer in AVAILABLE_LAYERS:
        if layer.id == layer_id:
            return layer
    raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")


@router.get("/{layer_id}/preview")
async def get_layer_preview(
    layer_id: str,
    lat: float = Query(..., description="Center latitude"),
    lng: float = Query(..., description="Center longitude"),
    scale: int = Query(2500, description="Map scale (e.g., 2500 for 1:2500)"),
    width: int = Query(800, ge=100, le=4096, description="Image width in pixels"),
    height: int = Query(600, ge=100, le=4096, description="Image height in pixels")
):
    """
    Get a map preview image for a layer at specified location
    """
    # Find layer config
    layer_config = None
    for layer in AVAILABLE_LAYERS:
        if layer.id == layer_id:
            layer_config = layer
            break

    if not layer_config:
        raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")

    # Calculate bounding box based on scale
    # A3 landscape is 420mm x 297mm
    # Scale 1:2500 means 1mm on map = 2.5m in reality
    paper_width_m = 0.420 * scale  # Map extent in meters
    paper_height_m = 0.297 * scale

    # Convert to degrees (approximate for Netherlands)
    lat_deg_per_m = 1 / 111320
    lng_deg_per_m = 1 / (111320 * 0.65)  # cos(52 deg) ~ 0.65

    half_width = (paper_width_m / 2) * lng_deg_per_m
    half_height = (paper_height_m / 2) * lat_deg_per_m

    bbox = f"{lng - half_width},{lat - half_height},{lng + half_width},{lat + half_height}"

    # Build WMS GetMap request
    if layer_config.type == "WMS":
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetMap",
            "LAYERS": layer_config.layer,
            "CRS": "EPSG:4326",
            "BBOX": bbox,
            "WIDTH": width,
            "HEIGHT": height,
            "FORMAT": "image/png",
            "TRANSPARENT": "true"
        }
        url = layer_config.url
    else:
        # For WMTS, we would need to calculate tile coordinates
        # For now, return a placeholder
        raise HTTPException(status_code=501, detail="WMTS preview not yet implemented")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"WMS service error: {str(e)}")

    return StreamingResponse(
        BytesIO(response.content),
        media_type="image/png"
    )

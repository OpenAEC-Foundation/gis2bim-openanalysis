"""
Geocoding API - Address search using PDOK Locatieserver
"""
from fastapi import APIRouter, HTTPException, Query
import httpx
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

PDOK_LOCATIESERVER_URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1"


class GeocodingResult(BaseModel):
    """Single geocoding result"""
    address: str
    municipality: Optional[str] = None
    province: Optional[str] = None
    lat: float
    lng: float
    rd_x: Optional[float] = None
    rd_y: Optional[float] = None
    type: str
    score: float


class GeocodingResponse(BaseModel):
    """Geocoding response"""
    results: List[GeocodingResult]
    total: int


@router.get("/search", response_model=GeocodingResponse)
async def search_address(
    q: str = Query(..., min_length=2, description="Search query"),
    rows: int = Query(5, ge=1, le=20, description="Number of results")
):
    """
    Search for addresses using PDOK Locatieserver
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{PDOK_LOCATIESERVER_URL}/free",
                params={"q": q, "rows": rows}
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"PDOK service error: {str(e)}")

    results = []
    for doc in data.get("response", {}).get("docs", []):
        # Parse centroid coordinates
        centroid = doc.get("centroide_ll", "")
        lat, lng = 0.0, 0.0
        if centroid:
            import re
            match = re.search(r"POINT\(([\d.]+) ([\d.]+)\)", centroid)
            if match:
                lng = float(match.group(1))
                lat = float(match.group(2))

        # Parse RD coordinates
        rd_centroid = doc.get("centroide_rd", "")
        rd_x, rd_y = None, None
        if rd_centroid:
            match = re.search(r"POINT\(([\d.]+) ([\d.]+)\)", rd_centroid)
            if match:
                rd_x = float(match.group(1))
                rd_y = float(match.group(2))

        results.append(GeocodingResult(
            address=doc.get("weergavenaam", ""),
            municipality=doc.get("gemeentenaam"),
            province=doc.get("provincienaam"),
            lat=lat,
            lng=lng,
            rd_x=rd_x,
            rd_y=rd_y,
            type=doc.get("type", "unknown"),
            score=doc.get("score", 0.0)
        ))

    return GeocodingResponse(
        results=results,
        total=data.get("response", {}).get("numFound", 0)
    )


@router.get("/reverse")
async def reverse_geocode(
    lat: float = Query(..., description="Latitude (WGS84)"),
    lng: float = Query(..., description="Longitude (WGS84)")
):
    """
    Reverse geocode coordinates to address
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{PDOK_LOCATIESERVER_URL}/reverse",
                params={"lat": lat, "lon": lng, "rows": 1}
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"PDOK service error: {str(e)}")

    docs = data.get("response", {}).get("docs", [])
    if not docs:
        return {"address": None, "municipality": None}

    doc = docs[0]
    return {
        "address": doc.get("weergavenaam"),
        "municipality": doc.get("gemeentenaam"),
        "province": doc.get("provincienaam"),
        "type": doc.get("type")
    }

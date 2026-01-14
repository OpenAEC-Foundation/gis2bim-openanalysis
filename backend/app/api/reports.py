"""
Reports API - Generate PDF reports
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from io import BytesIO
import uuid
from datetime import datetime
from pathlib import Path
import asyncio
import httpx

from app.services.pdf_generator import PDFGenerator
from app.services.map_service import MapService
from app.services.analysis_service import get_location_analysis

router = APIRouter()

# Store for report generation status
report_jobs = {}


class PageConfig(BaseModel):
    """Configuration for a single report page"""
    layer_id: str
    title: str
    subtitle: Optional[str] = None
    scale: int = 2500
    overlay_layers: List[str] = Field(default_factory=list)


class ReportRequest(BaseModel):
    """Request to generate a report"""
    lat: float = Field(..., description="Center latitude (WGS84)")
    lng: float = Field(..., description="Center longitude (WGS84)")
    address: Optional[str] = None
    municipality: Optional[str] = None
    paper_size: str = Field(default="A3", pattern="^(A3|A4)$")
    orientation: str = Field(default="landscape", pattern="^(landscape|portrait)$")
    pages: List[PageConfig] = Field(..., min_length=1)


class ReportStatus(BaseModel):
    """Status of a report generation job"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# Standard report template
STANDARD_REPORT_PAGES = [
    PageConfig(layer_id="top10nl", title="Topografische Kaart", subtitle="TOP10NL Basiskaart", scale=2500),
    PageConfig(layer_id="kadastrale-kaart", title="Kadastrale Kaart + BAG", subtitle="Percelen en Gebouwen", scale=1000, overlay_layers=["bag-panden"]),
    PageConfig(layer_id="bgt", title="BGT Grootschalige Topografie", subtitle="Basisregistratie", scale=500),
    PageConfig(layer_id="bestemmingsplan", title="Bestemmingsplan", subtitle="Ruimtelijke Plannen", scale=2500),
    PageConfig(layer_id="geluidkaart-weg", title="Geluidsbelasting", subtitle="Weg- en Railverkeer", scale=5000),
    PageConfig(layer_id="ahn3-dsm", title="AHN Hoogtekaart", subtitle="Actueel Hoogtebestand", scale=1000),
    PageConfig(layer_id="luchtfoto-actueel", title="Luchtfoto Overzicht", subtitle="Schaal 1:50.000", scale=50000),
    PageConfig(layer_id="luchtfoto-actueel", title="Luchtfoto Omgeving", subtitle="Schaal 1:5.000", scale=5000),
    PageConfig(layer_id="luchtfoto-actueel", title="Luchtfoto Detail", subtitle="Schaal 1:500", scale=500),
    PageConfig(layer_id="bodemkaart", title="Bodemkaart", subtitle="Bodemtypen en Grondsoorten", scale=5000),
    PageConfig(layer_id="rijksmonumenten", title="Cultuurhistorie", subtitle="Monumenten en Erfgoed", scale=2500),
    PageConfig(layer_id="waterschappen", title="Waterbeheer", subtitle="Waterschappen en Risico", scale=10000),
    PageConfig(layer_id="natura2000", title="Natuurbescherming", subtitle="Natura 2000 en NNN", scale=25000),
    PageConfig(layer_id="energielabels", title="Energie & Statistiek", subtitle="Energielabels en CBS", scale=2500),
    PageConfig(layer_id="samenvatting", title="Samenvatting", subtitle="Overzicht en Bronvermelding", scale=5000),
]


@router.get("/template")
async def get_standard_template():
    """Get the standard report template with 15 pages"""
    return {
        "name": "Standaard Locatie Rapport",
        "description": "Compleet overzicht van een locatie met alle relevante geodata",
        "pages": [page.model_dump() for page in STANDARD_REPORT_PAGES]
    }


@router.post("/generate", response_model=ReportStatus)
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Start generating a PDF report
    Returns a job ID that can be used to check status
    """
    job_id = str(uuid.uuid4())

    report_jobs[job_id] = ReportStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Report generation queued",
        created_at=datetime.now()
    )

    # Start background task
    background_tasks.add_task(
        generate_report_task,
        job_id,
        request
    )

    return report_jobs[job_id]


async def generate_report_task(job_id: str, request: ReportRequest):
    """Background task to generate the report"""
    try:
        report_jobs[job_id].status = "processing"
        report_jobs[job_id].message = "Fetching map images..."

        # Initialize services
        map_service = MapService()
        pdf_generator = PDFGenerator(
            paper_size=request.paper_size,
            orientation=request.orientation
        )

        total_pages = len(request.pages)

        for i, page_config in enumerate(request.pages):
            # Update progress
            progress = int((i / total_pages) * 100)
            report_jobs[job_id].progress = progress
            report_jobs[job_id].message = f"Generating page {i + 1}/{total_pages}: {page_config.title}"

            # Fetch map image
            map_image = await map_service.get_map_image(
                layer_id=page_config.layer_id,
                lat=request.lat,
                lng=request.lng,
                scale=page_config.scale,
                overlay_layers=page_config.overlay_layers
            )

            # Add page to PDF
            pdf_generator.add_page(
                title=page_config.title,
                subtitle=page_config.subtitle,
                map_image=map_image,
                location={
                    "address": request.address,
                    "municipality": request.municipality,
                    "lat": request.lat,
                    "lng": request.lng
                },
                scale=page_config.scale,
                page_number=i + 1,
                total_pages=total_pages
            )

            # Small delay to prevent overwhelming services
            await asyncio.sleep(0.1)

        # Generate final PDF
        report_jobs[job_id].message = "Generating PDF..."
        output_path = pdf_generator.save(f"report_{job_id}.pdf")

        report_jobs[job_id].status = "completed"
        report_jobs[job_id].progress = 100
        report_jobs[job_id].message = "Report generated successfully"
        report_jobs[job_id].download_url = f"/api/reports/download/{job_id}"
        report_jobs[job_id].completed_at = datetime.now()

    except Exception as e:
        report_jobs[job_id].status = "failed"
        report_jobs[job_id].message = f"Error: {str(e)}"


@router.get("/status/{job_id}", response_model=ReportStatus)
async def get_report_status(job_id: str):
    """Get the status of a report generation job"""
    if job_id not in report_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return report_jobs[job_id]


@router.get("/download/{job_id}")
async def download_report(job_id: str):
    """Download a completed report"""
    if job_id not in report_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = report_jobs[job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Report not ready. Status: {job.status}")

    output_dir = Path("output")
    file_path = output_dir / f"report_{job_id}.pdf"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"GIS2BIM_Report_{job_id[:8]}.pdf"
    )


class DirectReportRequest(BaseModel):
    """Request to generate a report directly (synchronous)"""
    location: dict = Field(..., description="Location with lat, lng, address, municipality")
    paper_size: str = Field(default="A3", pattern="^(A3|A4)$")
    orientation: str = Field(default="landscape", pattern="^(landscape|portrait)$")
    pages: List[dict] = Field(..., min_length=1)


class AddressReportRequest(BaseModel):
    """Request to generate a report from an address (public API)"""
    address: str = Field(..., description="Dutch address to search for", min_length=3)
    paper_size: str = Field(default="A3", pattern="^(A3|A4)$")
    orientation: str = Field(default="landscape", pattern="^(landscape|portrait)$")
    report_type: str = Field(default="standard", description="Type of report: standard, quick, detailed")


@router.post("/generate-direct")
async def generate_report_direct(request: DirectReportRequest):
    """
    Generate and return PDF directly (synchronous)
    This is simpler but blocks - use /generate for async generation
    """
    from io import BytesIO

    try:
        # Initialize services
        map_service = MapService()
        pdf_generator = PDFGenerator(
            paper_size=request.paper_size,
            orientation=request.orientation
        )

        total_pages = len(request.pages)
        lat = request.location.get("lat", 52.0)
        lng = request.location.get("lng", 5.0)

        for i, page_config in enumerate(request.pages):
            layer_id = page_config.get("layer_id", "")

            # Special handling for analysis/summary page
            if layer_id == "samenvatting" or layer_id == "analysis":
                # Fetch analysis data
                try:
                    analysis_data = await get_location_analysis(lat=lat, lng=lng, radius=500)
                    pdf_generator.add_analysis_page(
                        analysis_data=analysis_data,
                        location=request.location,
                        page_number=i + 1,
                        total_pages=total_pages
                    )
                except Exception as e:
                    print(f"[Report] Error fetching analysis: {e}")
                    # Add placeholder page if analysis fails
                    pdf_generator.add_page(
                        title="Locatie Analyse",
                        subtitle="Data niet beschikbaar",
                        map_image=None,
                        location=request.location,
                        scale=2500,
                        page_number=i + 1,
                        total_pages=total_pages
                    )
                continue

            # Fetch map image
            map_image = await map_service.get_map_image(
                layer_id=layer_id,
                lat=lat,
                lng=lng,
                scale=page_config.get("scale", 2500),
                overlay_layers=page_config.get("overlay_layers", []),
                paper_size=request.paper_size,
                orientation=request.orientation
            )

            # Add page to PDF
            pdf_generator.add_page(
                title=page_config.get("title", f"Pagina {i+1}"),
                subtitle=page_config.get("subtitle"),
                map_image=map_image,
                location=request.location,
                scale=page_config.get("scale", 2500),
                page_number=i + 1,
                total_pages=total_pages
            )

        # Get PDF bytes
        pdf_bytes = pdf_generator.get_bytes()

        # Clean up
        await map_service.close()

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=GIS2BIM_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


# Report templates for public API
REPORT_TEMPLATES = {
    "quick": [
        {"layer_id": "luchtfoto-actueel", "title": "Luchtfoto", "scale": 2500},
        {"layer_id": "kadastrale-kaart", "title": "Kadastrale Kaart", "scale": 1000},
        {"layer_id": "bestemmingsplan", "title": "Bestemmingsplan", "scale": 2500},
        {"layer_id": "samenvatting", "title": "Locatie Analyse", "scale": 0},
    ],
    "standard": [
        {"layer_id": "top10nl", "title": "Topografische Kaart", "scale": 2500},
        {"layer_id": "luchtfoto-actueel", "title": "Luchtfoto", "scale": 2500},
        {"layer_id": "kadastrale-kaart", "title": "Kadastrale Kaart", "scale": 1000, "overlay_layers": ["bag-panden"]},
        {"layer_id": "bestemmingsplan", "title": "Bestemmingsplan", "scale": 2500},
        {"layer_id": "ahn-dsm", "title": "Hoogtekaart (AHN)", "scale": 1000},
        {"layer_id": "bodemkaart", "title": "Bodemkaart", "scale": 5000},
        {"layer_id": "samenvatting", "title": "Locatie Analyse", "scale": 0},
    ],
    "detailed": [
        {"layer_id": "top10nl", "title": "Topografische Kaart", "scale": 2500},
        {"layer_id": "luchtfoto-actueel", "title": "Luchtfoto Overzicht", "scale": 5000},
        {"layer_id": "luchtfoto-actueel", "title": "Luchtfoto Detail", "scale": 500},
        {"layer_id": "kadastrale-kaart", "title": "Kadastrale Kaart", "scale": 1000, "overlay_layers": ["bag-panden"]},
        {"layer_id": "bestemmingsplan", "title": "Bestemmingsplan", "scale": 2500},
        {"layer_id": "ahn-dsm", "title": "Hoogtekaart DSM", "scale": 1000},
        {"layer_id": "ahn-dtm", "title": "Hoogtekaart DTM", "scale": 1000},
        {"layer_id": "bodemkaart", "title": "Bodemkaart", "scale": 5000},
        {"layer_id": "natura2000", "title": "Natura 2000", "scale": 25000},
        {"layer_id": "gemeentegrenzen", "title": "Bestuurlijke Grenzen", "scale": 25000},
        {"layer_id": "samenvatting", "title": "Locatie Analyse", "scale": 0},
    ]
}


@router.post("/from-address")
async def generate_report_from_address(request: AddressReportRequest):
    """
    Public API: Generate a PDF report from a Dutch address.

    This endpoint:
    1. Searches for the address using PDOK Locatieserver
    2. Gets the coordinates
    3. Generates a PDF report with the specified template
    4. Returns the PDF

    Example:
        POST /api/reports/from-address
        {
            "address": "Grote Kerk 1, Dordrecht",
            "paper_size": "A3",
            "orientation": "landscape",
            "report_type": "standard"
        }
    """
    # Step 1: Geocode the address
    geocode_url = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                geocode_url,
                params={"q": request.address, "rows": 1, "fq": "type:adres"}
            )

            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Geocoding service unavailable")

            data = response.json()

            if not data.get("response", {}).get("docs"):
                raise HTTPException(status_code=404, detail=f"Address not found: {request.address}")

            result = data["response"]["docs"][0]

            # Parse coordinates from centroide_ll (format: "POINT(lng lat)")
            centroid = result.get("centroide_ll", "")
            if centroid.startswith("POINT("):
                coords = centroid[6:-1].split()
                lng = float(coords[0])
                lat = float(coords[1])
            else:
                raise HTTPException(status_code=500, detail="Could not parse coordinates")

            address = result.get("weergavenaam", request.address)
            municipality = result.get("gemeentenaam", "")

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Geocoding service timeout")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding error: {str(e)}")

    # Step 2: Get the report template
    pages = REPORT_TEMPLATES.get(request.report_type, REPORT_TEMPLATES["standard"])

    # Step 3: Generate the PDF
    try:
        map_service = MapService()
        pdf_generator = PDFGenerator(
            paper_size=request.paper_size,
            orientation=request.orientation
        )

        total_pages = len(pages)

        location_data = {
            "address": address,
            "municipality": municipality,
            "lat": lat,
            "lng": lng
        }

        for i, page_config in enumerate(pages):
            layer_id = page_config.get("layer_id", "")

            # Special handling for analysis/summary page
            if layer_id == "samenvatting" or layer_id == "analysis":
                try:
                    analysis_data = await get_location_analysis(lat=lat, lng=lng, radius=500)
                    pdf_generator.add_analysis_page(
                        analysis_data=analysis_data,
                        location=location_data,
                        page_number=i + 1,
                        total_pages=total_pages
                    )
                except Exception as e:
                    print(f"[Report] Error fetching analysis: {e}")
                    pdf_generator.add_page(
                        title="Locatie Analyse",
                        subtitle="Data niet beschikbaar",
                        map_image=None,
                        location=location_data,
                        scale=2500,
                        page_number=i + 1,
                        total_pages=total_pages
                    )
                continue

            map_image = await map_service.get_map_image(
                layer_id=layer_id,
                lat=lat,
                lng=lng,
                scale=page_config.get("scale", 2500),
                overlay_layers=page_config.get("overlay_layers", []),
                paper_size=request.paper_size,
                orientation=request.orientation
            )

            pdf_generator.add_page(
                title=page_config.get("title", f"Pagina {i+1}"),
                subtitle=page_config.get("subtitle"),
                map_image=map_image,
                location={
                    "address": address,
                    "municipality": municipality,
                    "lat": lat,
                    "lng": lng
                },
                scale=page_config.get("scale", 2500),
                page_number=i + 1,
                total_pages=total_pages
            )

        pdf_bytes = pdf_generator.get_bytes()
        await map_service.close()

        # Generate filename from address
        safe_address = "".join(c if c.isalnum() or c in " -_" else "_" for c in address[:50])

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="OpenAnalysis_{safe_address}_{datetime.now().strftime("%Y%m%d")}.pdf"'
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/templates")
async def get_report_templates():
    """Get available report templates for the public API"""
    return {
        "templates": {
            name: {
                "pages": len(pages),
                "layers": [p["layer_id"] for p in pages],
                "description": {
                    "quick": "Snelle rapportage met 3 kaarten (luchtfoto, kadaster, bestemmingsplan)",
                    "standard": "Standaard rapportage met 6 kaarten",
                    "detailed": "Uitgebreide rapportage met 10 kaarten"
                }.get(name, "")
            }
            for name, pages in REPORT_TEMPLATES.items()
        }
    }


class DXFRequest(BaseModel):
    """Request to generate a DXF file with cadastral data"""
    lat: float = Field(..., description="Center latitude (WGS84)")
    lng: float = Field(..., description="Center longitude (WGS84)")
    radius: float = Field(default=250, description="Radius in meters (half of bounding box)")
    layers: List[str] = Field(
        default=["Perceel", "OpenbareRuimteNaam"],
        description="Kadaster WFS layers to include"
    )


@router.post("/download-dxf")
async def download_cadastral_dxf(request: DXFRequest):
    """
    Download cadastral (Kadaster) data as DXF file.

    This endpoint fetches cadastral data from PDOK Kadaster WFS and
    converts it to DXF format for use in CAD software.

    Available layers:
    - Perceel: Cadastral parcels with boundaries
    - OpenbareRuimteNaam: Public space names (streets, squares)
    - Bebouwing: Buildings (from cadastral registration)

    Example:
        POST /api/reports/download-dxf
        {
            "lat": 51.8133,
            "lng": 4.6601,
            "radius": 250,
            "layers": ["Perceel", "OpenbareRuimteNaam"]
        }
    """
    from app.services.dxf_generator import generate_cadastral_dxf

    try:
        # Generate DXF
        dxf_bytes = await generate_cadastral_dxf(
            lat=request.lat,
            lng=request.lng,
            radius=request.radius,
            layers=request.layers
        )

        # Return DXF file
        return StreamingResponse(
            BytesIO(dxf_bytes),
            media_type="application/dxf",
            headers={
                "Content-Disposition": f"attachment; filename=kadaster_{request.lat:.5f}_{request.lng:.5f}.dxf"
            }
        )

    except Exception as e:
        print(f"[DXF] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating DXF: {str(e)}")


class AnalysisRequest(BaseModel):
    """Request for location analysis data"""
    lat: float = Field(..., description="Latitude (WGS84)")
    lng: float = Field(..., description="Longitude (WGS84)")
    radius: float = Field(default=500, description="Search radius in meters")


@router.post("/analysis")
async def get_analysis(request: AnalysisRequest):
    """
    Get analysis data for a location.

    Returns statistics about:
    - Buildings (count, age distribution, building year)
    - Cadastral parcels (count, area)
    - Neighborhood data (inhabitants, households, municipality)

    Example:
        POST /api/reports/analysis
        {
            "lat": 51.8133,
            "lng": 4.6601,
            "radius": 500
        }
    """
    try:
        analysis = await get_location_analysis(
            lat=request.lat,
            lng=request.lng,
            radius=request.radius
        )
        return analysis
    except Exception as e:
        print(f"[Analysis] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching analysis: {str(e)}")

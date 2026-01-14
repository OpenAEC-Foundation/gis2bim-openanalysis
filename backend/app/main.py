"""
GIS2BIM OpenAnalysis - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api import reports, geocoding, layers, servers, presets

# Create FastAPI app
app = FastAPI(
    title="GIS2BIM OpenAnalysis",
    description="Genereer locatie rapporten met Nederlandse geodata",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.1.0"}


# Include API routers
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(geocoding.router, prefix="/api/geocoding", tags=["geocoding"])
app.include_router(layers.router, prefix="/api/layers", tags=["layers"])
app.include_router(servers.router, prefix="/api/servers", tags=["servers"])
app.include_router(presets.router, prefix="/api/presets", tags=["presets"])

# Serve static files (frontend) - MUST be last!
frontend_path = Path(__file__).parent.parent.parent / "mockup"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

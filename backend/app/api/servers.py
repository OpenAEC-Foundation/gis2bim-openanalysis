"""
Servers API - Manage WMS/WMTS server configurations and GetCapabilities
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import httpx
import json
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

router = APIRouter()

# Path to servers config file
SERVERS_FILE = Path(__file__).parent.parent.parent.parent / "servers.json"


class ServerConfig(BaseModel):
    """Configuration for a WMS/WMTS server"""
    id: str
    name: str
    url: str
    type: str = "WMS"
    version: Optional[str] = "1.3.0"
    layers: List[str] = Field(default_factory=list)
    crs: List[str] = Field(default_factory=list)
    status: str = "active"
    description: Optional[str] = None


class ServersConfig(BaseModel):
    """Full servers configuration"""
    version: str = "1.0.0"
    lastUpdated: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    servers: List[ServerConfig] = Field(default_factory=list)


class CapabilitiesResponse(BaseModel):
    """Response from GetCapabilities"""
    server_id: str
    url: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    layers: List[Dict] = Field(default_factory=list)
    crs: List[str] = Field(default_factory=list)
    formats: List[str] = Field(default_factory=list)
    error: Optional[str] = None


def load_servers() -> ServersConfig:
    """Load servers configuration from file"""
    if SERVERS_FILE.exists():
        with open(SERVERS_FILE, 'r') as f:
            data = json.load(f)
            return ServersConfig(**data)
    return ServersConfig()


def save_servers(config: ServersConfig):
    """Save servers configuration to file"""
    config.lastUpdated = datetime.now().strftime("%Y-%m-%d")
    with open(SERVERS_FILE, 'w') as f:
        json.dump(config.model_dump(), f, indent=2)


@router.get("/", response_model=ServersConfig)
async def get_servers():
    """Get all configured servers"""
    return load_servers()


@router.get("/{server_id}", response_model=ServerConfig)
async def get_server(server_id: str):
    """Get a specific server configuration"""
    config = load_servers()
    for server in config.servers:
        if server.id == server_id:
            return server
    raise HTTPException(status_code=404, detail=f"Server {server_id} not found")


@router.post("/", response_model=ServerConfig)
async def add_server(server: ServerConfig):
    """Add a new server"""
    config = load_servers()

    # Check if server ID already exists
    for existing in config.servers:
        if existing.id == server.id:
            raise HTTPException(status_code=400, detail=f"Server with ID {server.id} already exists")

    config.servers.append(server)
    save_servers(config)
    return server


@router.put("/{server_id}", response_model=ServerConfig)
async def update_server(server_id: str, server: ServerConfig):
    """Update an existing server"""
    config = load_servers()

    for i, existing in enumerate(config.servers):
        if existing.id == server_id:
            config.servers[i] = server
            save_servers(config)
            return server

    raise HTTPException(status_code=404, detail=f"Server {server_id} not found")


@router.delete("/{server_id}")
async def delete_server(server_id: str):
    """Delete a server"""
    config = load_servers()

    for i, existing in enumerate(config.servers):
        if existing.id == server_id:
            del config.servers[i]
            save_servers(config)
            return {"message": f"Server {server_id} deleted"}

    raise HTTPException(status_code=404, detail=f"Server {server_id} not found")


@router.get("/{server_id}/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(server_id: str):
    """Fetch GetCapabilities for a server"""
    config = load_servers()

    server = None
    for s in config.servers:
        if s.id == server_id:
            server = s
            break

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    if server.type == "TILE":
        return CapabilitiesResponse(
            server_id=server_id,
            url=server.url,
            title=server.name,
            abstract="Tile service - no GetCapabilities available",
            layers=[{"name": l, "title": l} for l in server.layers],
            crs=server.crs,
            formats=["image/png"]
        )

    # Fetch GetCapabilities for WMS
    capabilities_url = f"{server.url}?SERVICE=WMS&VERSION={server.version}&REQUEST=GetCapabilities"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(capabilities_url)

            if response.status_code != 200:
                return CapabilitiesResponse(
                    server_id=server_id,
                    url=server.url,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )

            # Parse XML response
            return parse_wms_capabilities(server_id, server.url, response.text)

    except Exception as e:
        return CapabilitiesResponse(
            server_id=server_id,
            url=server.url,
            error=f"{type(e).__name__}: {str(e)}"
        )


def parse_wms_capabilities(server_id: str, url: str, xml_text: str) -> CapabilitiesResponse:
    """Parse WMS GetCapabilities XML response"""
    try:
        # Remove namespace for easier parsing
        xml_text = xml_text.replace('xmlns=', 'xmlns_original=')
        root = ET.fromstring(xml_text)

        # Find service metadata
        service = root.find('.//Service')
        title = service.find('Title').text if service is not None and service.find('Title') is not None else None
        abstract = service.find('Abstract').text if service is not None and service.find('Abstract') is not None else None

        # Find capability
        capability = root.find('.//Capability')

        # Get supported formats
        formats = []
        for get_map in root.findall('.//GetMap//Format'):
            if get_map.text:
                formats.append(get_map.text)

        # Get layers
        layers = []
        crs_set = set()

        for layer in root.findall('.//Layer'):
            layer_name = layer.find('Name')
            layer_title = layer.find('Title')

            if layer_name is not None and layer_name.text:
                layer_info = {
                    "name": layer_name.text,
                    "title": layer_title.text if layer_title is not None else layer_name.text,
                    "queryable": layer.get('queryable') == '1'
                }

                # Get abstract if available
                layer_abstract = layer.find('Abstract')
                if layer_abstract is not None and layer_abstract.text:
                    layer_info["abstract"] = layer_abstract.text

                # Get bounding box if available
                bbox = layer.find('BoundingBox')
                if bbox is not None:
                    layer_info["bbox"] = {
                        "minx": bbox.get('minx'),
                        "miny": bbox.get('miny'),
                        "maxx": bbox.get('maxx'),
                        "maxy": bbox.get('maxy')
                    }

                layers.append(layer_info)

            # Collect CRS
            for crs in layer.findall('CRS'):
                if crs.text:
                    crs_set.add(crs.text)
            for srs in layer.findall('SRS'):
                if srs.text:
                    crs_set.add(srs.text)

        return CapabilitiesResponse(
            server_id=server_id,
            url=url,
            title=title,
            abstract=abstract,
            layers=layers,
            crs=list(crs_set),
            formats=formats
        )

    except ET.ParseError as e:
        return CapabilitiesResponse(
            server_id=server_id,
            url=url,
            error=f"XML Parse Error: {str(e)}"
        )


@router.post("/check-all")
async def check_all_servers():
    """Check status of all servers"""
    config = load_servers()
    results = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for server in config.servers:
            status = "unknown"
            error = None

            try:
                if server.type == "TILE":
                    # For tile servers, try to fetch a sample tile
                    test_url = server.url.replace("{z}", "10").replace("{x}", "526").replace("{y}", "337")
                    response = await client.get(test_url)
                    status = "online" if response.status_code == 200 else "offline"
                else:
                    # For WMS, try GetCapabilities
                    test_url = f"{server.url}?SERVICE=WMS&REQUEST=GetCapabilities"
                    response = await client.get(test_url)
                    status = "online" if response.status_code == 200 else "offline"

            except Exception as e:
                status = "offline"
                error = str(e)

            results.append({
                "id": server.id,
                "name": server.name,
                "url": server.url,
                "status": status,
                "error": error
            })

    return {"servers": results}

"""
Presets API - Manage report presets/templates for different user types
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import json
from pathlib import Path
from datetime import datetime

router = APIRouter()

# Path to presets config file
PRESETS_FILE = Path(__file__).parent.parent.parent.parent / "presets.json"


class LayerConfig(BaseModel):
    """Configuration for a layer in a preset"""
    serverId: str
    layer: str
    title: str
    order: int
    style: Optional[str] = None
    opacity: Optional[float] = 1.0


class PageFormat(BaseModel):
    """Page format configuration"""
    size: str = "A3"
    orientation: str = "landscape"


class PresetConfig(BaseModel):
    """Configuration for a report preset"""
    id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    layers: List[LayerConfig] = Field(default_factory=list)
    analysisLayers: List[str] = Field(default_factory=list)
    pageFormat: PageFormat = Field(default_factory=PageFormat)
    custom: bool = False


class PresetsConfig(BaseModel):
    """Full presets configuration"""
    version: str = "1.0.0"
    lastUpdated: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    presets: List[PresetConfig] = Field(default_factory=list)
    defaultPreset: str = "architect"


def load_presets() -> PresetsConfig:
    """Load presets configuration from file"""
    if PRESETS_FILE.exists():
        with open(PRESETS_FILE, 'r') as f:
            data = json.load(f)
            return PresetsConfig(**data)
    return PresetsConfig()


def save_presets(config: PresetsConfig):
    """Save presets configuration to file"""
    config.lastUpdated = datetime.now().strftime("%Y-%m-%d")
    with open(PRESETS_FILE, 'w') as f:
        json.dump(config.model_dump(), f, indent=2)


@router.get("/", response_model=PresetsConfig)
async def get_presets():
    """Get all configured presets"""
    return load_presets()


@router.get("/{preset_id}", response_model=PresetConfig)
async def get_preset(preset_id: str):
    """Get a specific preset configuration"""
    config = load_presets()
    for preset in config.presets:
        if preset.id == preset_id:
            return preset
    raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")


@router.post("/", response_model=PresetConfig)
async def create_preset(preset: PresetConfig):
    """Create a new custom preset"""
    config = load_presets()

    # Check if preset ID already exists
    for existing in config.presets:
        if existing.id == preset.id:
            raise HTTPException(status_code=400, detail=f"Preset with ID {preset.id} already exists")

    preset.custom = True
    config.presets.append(preset)
    save_presets(config)
    return preset


@router.put("/{preset_id}", response_model=PresetConfig)
async def update_preset(preset_id: str, preset: PresetConfig):
    """Update an existing preset"""
    config = load_presets()

    for i, existing in enumerate(config.presets):
        if existing.id == preset_id:
            # Keep custom flag based on original
            preset.custom = existing.custom
            config.presets[i] = preset
            save_presets(config)
            return preset

    raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")


@router.delete("/{preset_id}")
async def delete_preset(preset_id: str):
    """Delete a custom preset (cannot delete built-in presets)"""
    config = load_presets()

    for i, existing in enumerate(config.presets):
        if existing.id == preset_id:
            if not existing.custom:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete built-in preset {preset_id}"
                )
            del config.presets[i]
            save_presets(config)
            return {"message": f"Preset {preset_id} deleted"}

    raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")


@router.post("/{preset_id}/duplicate", response_model=PresetConfig)
async def duplicate_preset(preset_id: str, new_name: str):
    """Duplicate a preset with a new name"""
    config = load_presets()

    source_preset = None
    for preset in config.presets:
        if preset.id == preset_id:
            source_preset = preset
            break

    if not source_preset:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    # Create new preset ID from name
    new_id = new_name.lower().replace(" ", "-")

    # Check if new ID already exists
    for existing in config.presets:
        if existing.id == new_id:
            raise HTTPException(status_code=400, detail=f"Preset with ID {new_id} already exists")

    # Create new preset
    new_preset = PresetConfig(
        id=new_id,
        name=new_name,
        description=source_preset.description,
        icon=source_preset.icon,
        layers=source_preset.layers.copy(),
        analysisLayers=source_preset.analysisLayers.copy(),
        pageFormat=source_preset.pageFormat,
        custom=True
    )

    config.presets.append(new_preset)
    save_presets(config)
    return new_preset


@router.put("/default/{preset_id}")
async def set_default_preset(preset_id: str):
    """Set the default preset"""
    config = load_presets()

    # Check if preset exists
    found = False
    for preset in config.presets:
        if preset.id == preset_id:
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    config.defaultPreset = preset_id
    save_presets(config)
    return {"message": f"Default preset set to {preset_id}", "defaultPreset": preset_id}

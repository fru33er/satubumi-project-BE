from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request body untuk membuat proyek baru."""

    name: str = Field(..., max_length=255, description="Nama proyek")
    description: str | None = Field(None, description="Deskripsi proyek")
    location_name: str = Field(..., max_length=255, description="Nama lokasi proyek")
    area_ha: float | None = Field(None, gt=0, description="Luas area proyek (ha)")
    status: str | None = Field(
        "active", description="Status: active, completed, suspended"
    )
    boundary_geojson: dict[str, Any] | None = Field(
        None, description="Batas wilayah proyek dalam format GeoJSON"
    )
    targets_json: dict[str, Any] | None = Field(
        None,
        description='Target proyek, contoh: {"restoration_ha": 1000, "tree_planting": 100000}',
    )


class ProjectUpdate(BaseModel):
    """Request body untuk mengupdate proyek (semua field opsional)."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    location_name: str | None = Field(None, max_length=255)
    area_ha: float | None = Field(None, gt=0)
    status: str | None = None
    boundary_geojson: dict[str, Any] | None = None
    targets_json: dict[str, Any] | None = None


class ProjectResponse(BaseModel):
    """Response schema untuk data proyek."""

    id: int
    name: str
    description: str | None = None
    location_name: str
    area_ha: float | None = None
    status: str
    boundary_geojson: dict[str, Any] | None = None
    targets_json: dict[str, Any] | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

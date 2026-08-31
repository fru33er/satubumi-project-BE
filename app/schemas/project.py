from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date


class ProjectCreate(BaseModel):
    """Request body untuk membuat proyek baru."""
    name: str = Field(..., max_length=255, description="Nama proyek")
    description: Optional[str] = Field(None, description="Deskripsi proyek")
    location_name: str = Field(..., max_length=255, description="Nama lokasi proyek")
    area_ha: Optional[float] = Field(None, gt=0, description="Luas area proyek (ha)")
    status: Optional[str] = Field("active", description="Status: active, completed, suspended")

    # Field baru
    project_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Tipe proyek: reforestation, mangrove, agroforestry, peatland, blue_carbon"
    )
    start_date: Optional[date] = Field(None, description="Tanggal mulai proyek")
    end_date: Optional[date] = Field(None, description="Tanggal selesai proyek")
    country: Optional[str] = Field("Indonesia", max_length=100, description="Negara")
    province: Optional[str] = Field(None, max_length=100, description="Provinsi")
    district: Optional[str] = Field(None, max_length=100, description="Kabupaten/Kota")

    boundary_geojson: Optional[Dict[str, Any]] = Field(
        None, description="Batas wilayah proyek dalam format GeoJSON Polygon"
    )
    targets_json: Optional[Dict[str, Any]] = Field(
        None,
        description='Target proyek, contoh: {"restoration_ha": 1000, "tree_planting": 100000}'
    )


class ProjectUpdate(BaseModel):
    """Request body untuk mengupdate proyek (semua field opsional)."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    location_name: Optional[str] = Field(None, max_length=255)
    area_ha: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None
    project_type: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    country: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    boundary_geojson: Optional[Dict[str, Any]] = None
    targets_json: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    """Response schema untuk data proyek."""
    id: int
    name: str
    description: Optional[str] = None
    location_name: str
    area_ha: Optional[float] = None
    status: str
    project_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    country: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    boundary_geojson: Optional[Dict[str, Any]] = None
    targets_json: Optional[Dict[str, Any]] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

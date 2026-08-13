from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.rapid_fs import RapidFSResult


class SubmitterInfo(BaseModel):
    """Data kontak user yang menggunakan fitur Rapid Score."""
    submitter_name: Optional[str] = Field(None, max_length=255, description="Nama lengkap submitter")
    submitter_phone: Optional[str] = Field(None, max_length=50, description="Nomor telepon submitter")
    submitter_email: Optional[str] = Field(None, max_length=255, description="Email submitter")


class AssessmentSubmitRequest(SubmitterInfo):
    """
    Request body untuk POST /assessments.
    Gabungan data kontak submitter + seluruh hasil kalkulasi Rapid-FS.
    """
    # Referensi hasil kalkulasi dari endpoint /rapid-fs/calculate
    rapid_fs_result: RapidFSResult


class AssessmentResponse(BaseModel):
    """Response schema untuk GET /assessments (list & detail)."""
    id: int
    user_id: Optional[int] = None

    # Data kontak submitter
    submitter_name: Optional[str] = None
    submitter_phone: Optional[str] = None
    submitter_email: Optional[str] = None

    # Input proyek
    location_name: str
    area_ha: float
    ecosystem_type: str
    project_duration_years: int
    carbon_price_usd: float

    # Hasil karbon & finansial
    agb_ton: Optional[float] = None
    carbon_stock_tc: Optional[float] = None
    co2e_ton: Optional[float] = None
    acc_total_credits: Optional[float] = None
    gross_revenue_usd: Optional[float] = None
    total_cost_usd: Optional[float] = None
    net_revenue_usd: Optional[float] = None

    # Skor kelayakan
    feasibility_score: float
    feasibility_category: str

    # Detail JSON
    component_scores_json: Optional[Dict[str, Any]] = None
    cost_breakdown_json: Optional[Dict[str, Any]] = None
    geometry_geojson: Optional[Dict[str, Any]] = None
    recommendations_json: Optional[List[str]] = None

    created_at: datetime

    model_config = {"from_attributes": True}

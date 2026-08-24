from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, date


# ─────────────────────────────────────────────
# PROJECT ACTIVITY
# ─────────────────────────────────────────────

class ActivityCreate(BaseModel):
    """Request body untuk mencatat kegiatan proyek baru."""
    activity_type: str = Field(
        ...,
        description="Jenis kegiatan: planting, restoration, biodiversity_survey, community_development, fire_prevention, forest_protection"
    )
    activity_date: date = Field(..., description="Tanggal kegiatan")
    location_geojson: Optional[Dict[str, Any]] = Field(None, description="Lokasi kegiatan (GeoJSON Point/Polygon)")
    target: Optional[float] = Field(None, description="Target kegiatan")
    realization: Optional[float] = Field(None, description="Realisasi kegiatan")
    unit: Optional[str] = Field(None, max_length=50, description="Satuan: ha, trees, person, dll")
    executor: Optional[str] = Field(None, max_length=255, description="Nama pelaksana/tim")
    photo_urls: Optional[List[str]] = Field(None, description="List URL foto dokumentasi")
    notes: Optional[str] = Field(None, description="Catatan tambahan")


class ActivityResponse(BaseModel):
    id: int
    project_id: int
    activity_type: str
    activity_date: date
    location_geojson: Optional[Dict[str, Any]] = None
    target: Optional[float] = None
    realization: Optional[float] = None
    unit: Optional[str] = None
    executor: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# TREE RECORD
# ─────────────────────────────────────────────

class TreeRecordCreate(BaseModel):
    """Request body untuk menambah data tanam pohon."""
    plot_id: Optional[str] = Field(None, max_length=100, description="Kode plot, misal WK-023")
    species: str = Field(..., max_length=255, description="Jenis/spesies pohon")
    quantity: int = Field(..., gt=0, description="Jumlah pohon dalam batch ini")
    planting_date: date = Field(..., description="Tanggal penanaman")
    location_geojson: Optional[Dict[str, Any]] = Field(None, description="Lokasi plot (GeoJSON Point)")
    condition: Optional[str] = Field("healthy", description="Kondisi: healthy, stressed, dead")
    height_cm: Optional[float] = Field(None, description="Tinggi pohon (cm)")
    dbh_cm: Optional[float] = Field(None, description="Diameter Breast Height (cm)")
    is_alive: Optional[bool] = Field(True, description="Status hidup pohon")
    photo_urls: Optional[List[str]] = Field(None, description="List URL foto")
    notes: Optional[str] = None


class TreeRecordUpdate(BaseModel):
    """Request body untuk update kondisi pohon (monitoring berkala)."""
    condition: Optional[str] = Field(None, description="Kondisi: healthy, stressed, dead")
    height_cm: Optional[float] = None
    dbh_cm: Optional[float] = None
    is_alive: Optional[bool] = None
    photo_urls: Optional[List[str]] = None
    notes: Optional[str] = None


class TreeRecordResponse(BaseModel):
    id: int
    project_id: int
    plot_id: Optional[str] = None
    species: str
    quantity: int
    planting_date: date
    location_geojson: Optional[Dict[str, Any]] = None
    condition: str
    height_cm: Optional[float] = None
    dbh_cm: Optional[float] = None
    is_alive: bool
    photo_urls: Optional[List[str]] = None
    notes: Optional[str] = None
    last_monitored: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TreeSummary(BaseModel):
    """Agregat statistik pohon untuk dashboard."""
    trees_planted: int
    trees_survived: int
    trees_dead: int
    survival_rate: float  # Persentase (%)
    alert_triggered: bool = False  # True jika survival rate < threshold


# ─────────────────────────────────────────────
# FIELD REPORT
# ─────────────────────────────────────────────

class FieldReportCreate(BaseModel):
    """Request body untuk submit laporan lapangan."""
    officer_name: str = Field(..., max_length=255, description="Nama petugas lapangan")
    plot_id: Optional[str] = Field(None, max_length=100, description="Kode plot yang dimonitor")
    location_geojson: Optional[Dict[str, Any]] = Field(None, description="Koordinat GPS petugas (GeoJSON Point)")
    report_date: datetime = Field(..., description="Tanggal & waktu laporan")
    report_type: str = Field(
        ...,
        description="Jenis laporan: tree_monitoring, biodiversity, incident, general, community"
    )
    activity_description: Optional[str] = Field(None, description="Deskripsi kegiatan yang dilakukan")
    result_description: Optional[str] = Field(None, description="Hasil/temuan di lapangan")
    photo_urls: Optional[List[str]] = Field(None, description="List URL foto bukti lapangan")


class FieldReportResponse(BaseModel):
    id: int
    project_id: int
    officer_name: str
    plot_id: Optional[str] = None
    location_geojson: Optional[Dict[str, Any]] = None
    report_date: datetime
    report_type: str
    activity_description: Optional[str] = None
    result_description: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    created_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# ALERT
# ─────────────────────────────────────────────

class AlertCreate(BaseModel):
    """Request body untuk membuat alert secara manual."""
    alert_type: str = Field(
        ...,
        description="Tipe alert: deforestation, fire, land_cover_change, monitoring_overdue, low_tree_survival"
    )
    severity: Optional[str] = Field("medium", description="Severity: low, medium, high, critical")
    location_geojson: Optional[Dict[str, Any]] = Field(None, description="Lokasi kejadian (GeoJSON)")
    description: str = Field(..., description="Deskripsi detail alert")


class AlertUpdate(BaseModel):
    """Request body untuk update status alert."""
    is_read: Optional[bool] = None
    is_resolved: Optional[bool] = None


class AlertResponse(BaseModel):
    id: int
    project_id: int
    alert_type: str
    severity: str
    location_geojson: Optional[Dict[str, Any]] = None
    description: str
    is_read: bool
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    auto_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# BIODIVERSITY OBSERVATION
# ─────────────────────────────────────────────

class BiodiversityCreate(BaseModel):
    """Request body untuk mencatat observasi biodiversitas."""
    species_name: str = Field(..., max_length=255, description="Nama spesies")
    species_type: str = Field(..., description="Tipe: fauna, flora")
    location_geojson: Optional[Dict[str, Any]] = Field(None, description="Lokasi observasi (GeoJSON Point)")
    observed_date: date = Field(..., description="Tanggal observasi")
    habitat: Optional[str] = Field(None, max_length=255, description="Jenis habitat")
    observer: Optional[str] = Field(None, max_length=255, description="Nama observer")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL foto spesies")
    notes: Optional[str] = None


class BiodiversityResponse(BaseModel):
    id: int
    project_id: int
    species_name: str
    species_type: str
    location_geojson: Optional[Dict[str, Any]] = None
    observed_date: date
    habitat: Optional[str] = None
    observer: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BiodiversitySummary(BaseModel):
    """Ringkasan biodiversitas proyek."""
    total_observations: int
    unique_species: int
    fauna_count: int
    flora_count: int


# ─────────────────────────────────────────────
# COMMUNITY DATA
# ─────────────────────────────────────────────

class CommunityCreate(BaseModel):
    """Request body untuk mencatat data dampak komunitas."""
    village_name: str = Field(..., max_length=255, description="Nama desa")
    beneficiary_count: Optional[int] = Field(0, ge=0, description="Jumlah penerima manfaat")
    livelihood_groups: Optional[int] = Field(0, ge=0, description="Jumlah kelompok mata pencaharian")
    employment_count: Optional[int] = Field(0, ge=0, description="Jumlah tenaga kerja")
    community_investment: Optional[float] = Field(0.0, ge=0, description="Investasi ke komunitas (USD)")
    activity_type: Optional[str] = Field(None, max_length=100, description="Jenis kegiatan komunitas")
    description: Optional[str] = None
    date: Optional[date] = None


class CommunityResponse(BaseModel):
    id: int
    project_id: int
    village_name: str
    beneficiary_count: int
    livelihood_groups: int
    employment_count: int
    community_investment: float
    activity_type: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CommunitySummary(BaseModel):
    """Ringkasan dampak komunitas proyek."""
    total_villages: int
    total_beneficiaries: int
    total_livelihood_groups: int
    total_employment: int
    total_community_investment: float


# ─────────────────────────────────────────────
# CARBON RECORD
# ─────────────────────────────────────────────

class CarbonCreate(BaseModel):
    """
    Request body untuk input data karbon.
    CATATAN: Data ini adalah monitoring/estimation, bukan verified carbon credit.
    """
    period_start: date = Field(..., description="Awal periode monitoring")
    period_end: date = Field(..., description="Akhir periode monitoring")
    carbon_stock_tco2e: Optional[float] = Field(None, description="Total carbon stock (tCO2e)")
    biomass_ton: Optional[float] = Field(None, description="Total biomassa (ton)")
    estimated_co2e: Optional[float] = Field(None, description="Estimasi CO2 equivalent")
    carbon_change: Optional[float] = Field(None, description="Perubahan karbon vs periode sebelumnya")
    methodology: Optional[str] = Field(None, max_length=255, description="Metodologi perhitungan")
    notes: Optional[str] = None


class CarbonResponse(BaseModel):
    id: int
    project_id: int
    period_start: date
    period_end: date
    carbon_stock_tco2e: Optional[float] = None
    biomass_ton: Optional[float] = None
    estimated_co2e: Optional[float] = None
    carbon_change: Optional[float] = None
    methodology: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

class DashboardResponse(BaseModel):
    """Agregat lengkap semua data monitor untuk satu proyek."""
    project_id: int
    project_name: str
    project_status: str

    # Statistik area
    area_ha: Optional[float] = None

    # Statistik pohon
    trees_planted: int = 0
    trees_survived: int = 0
    trees_dead: int = 0
    survival_rate: Optional[float] = None

    # Karbon (data terbaru)
    carbon_stock_tco2e: Optional[float] = None
    estimated_co2e: Optional[float] = None

    # Biodiversitas
    species_recorded: int = 0

    # Komunitas
    total_beneficiaries: int = 0
    total_villages: int = 0
    total_livelihood_groups: int = 0

    # Progress kegiatan
    total_activities: int = 0
    recent_activities: List[Dict[str, Any]] = []

    # Alert aktif
    active_alerts: int = 0
    recent_alerts: List[Dict[str, Any]] = []

    # Field reports
    total_field_reports: int = 0
    last_field_report: Optional[datetime] = None

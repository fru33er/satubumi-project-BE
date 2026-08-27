from datetime import date as DateType, datetime as DateTimeType
from typing import Any

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# PROJECT ACTIVITY
# ─────────────────────────────────────────────


class ActivityCreate(BaseModel):
    """Request body untuk mencatat kegiatan proyek baru."""

    activity_type: str = Field(
        ...,
        description="Jenis kegiatan: planting, restoration, biodiversity_survey, community_development, fire_prevention, forest_protection",
    )
    activity_date: DateType = Field(..., description="Tanggal kegiatan")
    location_geojson: dict[str, Any] | None = Field(
        None, description="Lokasi kegiatan (GeoJSON Point/Polygon)"
    )
    target: float | None = Field(None, description="Target kegiatan")
    realization: float | None = Field(None, description="Realisasi kegiatan")
    unit: str | None = Field(
        None, max_length=50, description="Satuan: ha, trees, person, dll"
    )
    executor: str | None = Field(
        None, max_length=255, description="Nama pelaksana/tim"
    )
    photo_urls: list[str] | None = Field(
        None, description="List URL foto dokumentasi"
    )
    notes: str | None = Field(None, description="Catatan tambahan")


class ActivityResponse(BaseModel):
    id: int
    project_id: int
    activity_type: str
    activity_date: DateType
    location_geojson: dict[str, Any] | None = None
    target: float | None = None
    realization: float | None = None
    unit: str | None = None
    executor: str | None = None
    photo_urls: list[str] | None = None
    notes: str | None = None
    created_by: int | None = None
    created_at: DateTimeType
    updated_at: DateTimeType

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# TREE RECORD
# ─────────────────────────────────────────────


class TreeRecordCreate(BaseModel):
    """Request body untuk menambah data tanam pohon."""

    plot_id: str | None = Field(
        None, max_length=100, description="Kode plot, misal WK-023"
    )
    species: str = Field(..., max_length=255, description="Jenis/spesies pohon")
    quantity: int = Field(..., gt=0, description="Jumlah pohon dalam batch ini")
    planting_date: DateType = Field(..., description="Tanggal penanaman")
    location_geojson: dict[str, Any] | None = Field(
        None, description="Lokasi plot (GeoJSON Point)"
    )
    condition: str | None = Field(
        "healthy", description="Kondisi: healthy, stressed, dead"
    )
    height_cm: float | None = Field(None, description="Tinggi pohon (cm)")
    dbh_cm: float | None = Field(None, description="Diameter Breast Height (cm)")
    is_alive: bool | None = Field(True, description="Status hidup pohon")
    photo_urls: list[str] | None = Field(None, description="List URL foto")
    notes: str | None = None


class TreeRecordUpdate(BaseModel):
    """Request body untuk update kondisi pohon (monitoring berkala)."""

    condition: str | None = Field(
        None, description="Kondisi: healthy, stressed, dead"
    )
    height_cm: float | None = None
    dbh_cm: float | None = None
    is_alive: bool | None = None
    photo_urls: list[str] | None = None
    notes: str | None = None


class TreeRecordResponse(BaseModel):
    id: int
    project_id: int
    plot_id: str | None = None
    species: str
    quantity: int
    planting_date: DateType
    location_geojson: dict[str, Any] | None = None
    condition: str
    height_cm: float | None = None
    dbh_cm: float | None = None
    is_alive: bool
    photo_urls: list[str] | None = None
    notes: str | None = None
    last_monitored: DateTimeType | None = None
    created_at: DateTimeType
    updated_at: DateTimeType

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
    plot_id: str | None = Field(
        None, max_length=100, description="Kode plot yang dimonitor"
    )
    location_geojson: dict[str, Any] | None = Field(
        None, description="Koordinat GPS petugas (GeoJSON Point)"
    )
    report_date: DateTimeType = Field(..., description="Tanggal & waktu laporan")
    report_type: str = Field(
        ...,
        description="Jenis laporan: tree_monitoring, biodiversity, incident, general, community",
    )
    activity_description: str | None = Field(
        None, description="Deskripsi kegiatan yang dilakukan"
    )
    result_description: str | None = Field(
        None, description="Hasil/temuan di lapangan"
    )
    photo_urls: list[str] | None = Field(
        None, description="List URL foto bukti lapangan"
    )


class FieldReportResponse(BaseModel):
    id: int
    project_id: int
    officer_name: str
    plot_id: str | None = None
    location_geojson: dict[str, Any] | None = None
    report_date: DateTimeType
    report_type: str
    activity_description: str | None = None
    result_description: str | None = None
    photo_urls: list[str] | None = None
    created_by: int | None = None
    created_at: DateTimeType

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# ALERT
# ─────────────────────────────────────────────


class AlertCreate(BaseModel):
    """Request body untuk membuat alert secara manual."""

    alert_type: str = Field(
        ...,
        description="Tipe alert: deforestation, fire, land_cover_change, monitoring_overdue, low_tree_survival",
    )
    severity: str | None = Field(
        "medium", description="Severity: low, medium, high, critical"
    )
    location_geojson: dict[str, Any] | None = Field(
        None, description="Lokasi kejadian (GeoJSON)"
    )
    description: str = Field(..., description="Deskripsi detail alert")


class AlertUpdate(BaseModel):
    """Request body untuk update status alert."""

    is_read: bool | None = None
    is_resolved: bool | None = None


class AlertResponse(BaseModel):
    id: int
    project_id: int
    alert_type: str
    severity: str
    location_geojson: dict[str, Any] | None = None
    description: str
    is_read: bool
    is_resolved: bool
    resolved_at: DateTimeType | None = None
    auto_generated: bool
    created_at: DateTimeType

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# BIODIVERSITY OBSERVATION
# ─────────────────────────────────────────────


class BiodiversityCreate(BaseModel):
    """Request body untuk mencatat observasi biodiversitas."""

    species_name: str = Field(..., max_length=255, description="Nama spesies")
    species_type: str = Field(..., description="Tipe: fauna, flora")
    location_geojson: dict[str, Any] | None = Field(
        None, description="Lokasi observasi (GeoJSON Point)"
    )
    observed_date: DateType = Field(..., description="Tanggal observasi")
    habitat: str | None = Field(None, max_length=255, description="Jenis habitat")
    observer: str | None = Field(None, max_length=255, description="Nama observer")
    photo_url: str | None = Field(
        None, max_length=500, description="URL foto spesies"
    )
    notes: str | None = None


class BiodiversityResponse(BaseModel):
    id: int
    project_id: int
    species_name: str
    species_type: str
    location_geojson: dict[str, Any] | None = None
    observed_date: DateType
    habitat: str | None = None
    observer: str | None = None
    photo_url: str | None = None
    notes: str | None = None
    created_at: DateTimeType

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
    beneficiary_count: int | None = Field(
        0, ge=0, description="Jumlah penerima manfaat"
    )
    livelihood_groups: int | None = Field(
        0, ge=0, description="Jumlah kelompok mata pencaharian"
    )
    employment_count: int | None = Field(0, ge=0, description="Jumlah tenaga kerja")
    community_investment: float | None = Field(
        0.0, ge=0, description="Investasi ke komunitas (USD)"
    )
    activity_type: str | None = Field(
        None, max_length=100, description="Jenis kegiatan komunitas"
    )
    description: str | None = None
    date: DateType | None = None


class CommunityResponse(BaseModel):
    id: int
    project_id: int
    village_name: str
    beneficiary_count: int
    livelihood_groups: int
    employment_count: int
    community_investment: float
    activity_type: str | None = None
    description: str | None = None
    date: DateType | None = None
    created_at: DateTimeType

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

    period_start: DateType = Field(..., description="Awal periode monitoring")
    period_end: DateType = Field(..., description="Akhir periode monitoring")
    carbon_stock_tco2e: float | None = Field(
        None, description="Total carbon stock (tCO2e)"
    )
    biomass_ton: float | None = Field(None, description="Total biomassa (ton)")
    estimated_co2e: float | None = Field(None, description="Estimasi CO2 equivalent")
    carbon_change: float | None = Field(
        None, description="Perubahan karbon vs periode sebelumnya"
    )
    methodology: str | None = Field(
        None, max_length=255, description="Metodologi perhitungan"
    )
    notes: str | None = None


class CarbonResponse(BaseModel):
    id: int
    project_id: int
    period_start: DateType
    period_end: DateType
    carbon_stock_tco2e: float | None = None
    biomass_ton: float | None = None
    estimated_co2e: float | None = None
    carbon_change: float | None = None
    methodology: str | None = None
    notes: str | None = None
    created_at: DateTimeType

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
    area_ha: float | None = None

    # Statistik pohon
    trees_planted: int = 0
    trees_survived: int = 0
    trees_dead: int = 0
    survival_rate: float | None = None

    # Karbon (data terbaru)
    carbon_stock_tco2e: float | None = None
    estimated_co2e: float | None = None

    # Biodiversitas
    species_recorded: int = 0

    # Komunitas
    total_beneficiaries: int = 0
    total_villages: int = 0
    total_livelihood_groups: int = 0

    # Progress kegiatan
    total_activities: int = 0
    recent_activities: list[dict[str, Any]] = []

    # Alert aktif
    active_alerts: int = 0
    recent_alerts: list[dict[str, Any]] = []

    # Field reports
    total_field_reports: int = 0
    last_field_report: DateTimeType | None = None
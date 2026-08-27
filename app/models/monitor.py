from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.core.database import Base


class ProjectActivity(Base):
    """
    Mencatat kegiatan yang dilakukan dalam proyek.
    Contoh: penanaman, restorasi, biodiversity survey, community development.
    """

    __tablename__ = "project_activities"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Jenis kegiatan: planting, restoration, biodiversity_survey,
    # community_development, fire_prevention, forest_protection
    activity_type = Column(String(100), nullable=False)

    activity_date = Column(Date, nullable=False)
    location_geojson = Column(
        JSON, nullable=True
    )  # GeoJSON Point atau Polygon lokasi kegiatan

    # Target & realisasi (misalnya target 1000 ha, realisasi 650 ha)
    target = Column(Float, nullable=True)
    realization = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)  # "ha", "trees", "person", dll

    executor = Column(String(255), nullable=True)  # Nama pelaksana/tim
    photo_urls = Column(JSON, nullable=True)  # List URL foto dokumentasi
    notes = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TreeRecord(Base):
    """
    Data tanam per-batch atau per-plot untuk monitoring pohon/restorasi.
    Dashboard menghitung Trees Planted, Survived, Dead, Survival Rate dari tabel ini.
    """

    __tablename__ = "tree_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plot_id = Column(String(100), nullable=True)  # Kode plot, misal "WK-023"

    species = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)  # Jumlah pohon dalam batch ini
    planting_date = Column(Date, nullable=False)
    location_geojson = Column(JSON, nullable=True)  # GeoJSON Point lokasi plot

    # Data monitoring kondisi pohon
    condition = Column(String(50), default="healthy")  # healthy, stressed, dead
    height_cm = Column(Float, nullable=True)
    dbh_cm = Column(Float, nullable=True)  # Diameter Breast Height
    is_alive = Column(Boolean, default=True)

    photo_urls = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    last_monitored = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FieldReport(Base):
    """
    Laporan yang dikirim petugas lapangan secara langsung.
    Setiap laporan memiliki: WHO + WHERE + WHEN + WHAT + EVIDENCE.
    """

    __tablename__ = "field_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    officer_name = Column(String(255), nullable=False)
    plot_id = Column(String(100), nullable=True)
    location_geojson = Column(JSON, nullable=True)  # GPS Point dari petugas lapangan

    report_date = Column(DateTime, nullable=False)

    # Jenis laporan: tree_monitoring, biodiversity, incident, general, community
    report_type = Column(String(100), nullable=False)

    activity_description = Column(Text, nullable=True)
    result_description = Column(Text, nullable=True)
    photo_urls = Column(JSON, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """
    Peringatan terkait kondisi atau perubahan di wilayah proyek.
    Bisa dibuat manual (admin) atau auto-generated oleh sistem.
    """

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tipe alert: deforestation, fire, land_cover_change, monitoring_overdue, low_tree_survival
    alert_type = Column(String(100), nullable=False)

    # Severity: low, medium, high, critical
    severity = Column(String(50), default="medium", nullable=False)

    location_geojson = Column(JSON, nullable=True)
    description = Column(Text, nullable=False)

    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    # True jika alert dibuat otomatis oleh sistem (bukan manual dari admin)
    auto_generated = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class BiodiversityObservation(Base):
    """
    Hasil pengamatan biodiversitas (satwa/flora) di lokasi proyek.
    """

    __tablename__ = "biodiversity_observations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    species_name = Column(String(255), nullable=False)
    species_type = Column(String(50), nullable=False)  # fauna, flora
    location_geojson = Column(JSON, nullable=True)

    observed_date = Column(Date, nullable=False)
    habitat = Column(String(255), nullable=True)
    observer = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class CommunityData(Base):
    """
    Data dampak sosial & ekonomi proyek terhadap masyarakat sekitar.
    """

    __tablename__ = "community_data"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    village_name = Column(String(255), nullable=False)
    beneficiary_count = Column(Integer, default=0)
    livelihood_groups = Column(Integer, default=0)
    employment_count = Column(Integer, default=0)
    community_investment = Column(Float, default=0.0)  # Nilai investasi (USD)

    # Jenis kegiatan: pelatihan, agroforestry, livelihood, community_enterprise, dll
    activity_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class CarbonRecord(Base):
    """
    Estimasi dan monitoring data karbon per periode.
    CATATAN: Data ini adalah monitoring/estimation, bukan verified carbon credit.
    """

    __tablename__ = "carbon_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    carbon_stock_tco2e = Column(Float, nullable=True)  # Total carbon stock (tCO2e)
    biomass_ton = Column(Float, nullable=True)
    estimated_co2e = Column(Float, nullable=True)  # Estimasi CO2 equivalent
    carbon_change = Column(
        Float, nullable=True
    )  # Perubahan karbon vs periode sebelumnya

    methodology = Column(
        String(255), nullable=True
    )  # Metode perhitungan yang digunakan
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

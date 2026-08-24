from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.project import Project
from app.models.monitor import (
    ProjectActivity, TreeRecord, FieldReport,
    Alert, BiodiversityObservation, CommunityData, CarbonRecord
)
from app.models.user import User
from app.schemas.monitor import (
    ActivityCreate, ActivityResponse,
    TreeRecordCreate, TreeRecordUpdate, TreeRecordResponse, TreeSummary,
    FieldReportCreate, FieldReportResponse,
    AlertCreate, AlertUpdate, AlertResponse,
    BiodiversityCreate, BiodiversityResponse, BiodiversitySummary,
    CommunityCreate, CommunityResponse, CommunitySummary,
    CarbonCreate, CarbonResponse,
    DashboardResponse,
)
from app.api.v1.auth import get_current_user
from app.services.alert_service import check_and_create_survival_alert, check_and_create_overdue_alert

router = APIRouter(prefix="/projects", tags=["Monitor — Data"])


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def require_admin(current_user: User) -> User:
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin atau super_admin yang dapat melakukan aksi ini."
        )
    return current_user


def get_project_or_404(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")
    return project


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@router.get("/{project_id}/dashboard", response_model=DashboardResponse)
def get_dashboard(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dashboard agregat untuk satu proyek.

    Menampilkan ringkasan semua data monitor:
    statistik pohon, karbon, biodiversitas, komunitas,
    kegiatan terbaru, dan alert aktif.

    Endpoint ini juga men-trigger auto-check untuk alert monitoring_overdue.
    """
    project = get_project_or_404(project_id, db)

    # Auto-check monitoring overdue
    check_and_create_overdue_alert(db, project_id)

    # --- Statistik Pohon ---
    tree_records = db.query(TreeRecord).filter(TreeRecord.project_id == project_id).all()
    trees_planted = sum(r.quantity for r in tree_records)
    trees_survived = sum(r.quantity for r in tree_records if r.is_alive)
    trees_dead = trees_planted - trees_survived
    survival_rate = round((trees_survived / trees_planted * 100), 2) if trees_planted > 0 else None

    # --- Karbon (record terbaru) ---
    latest_carbon = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.project_id == project_id)
        .order_by(CarbonRecord.period_end.desc())
        .first()
    )

    # --- Biodiversitas ---
    species_recorded = (
        db.query(func.count(func.distinct(BiodiversityObservation.species_name)))
        .filter(BiodiversityObservation.project_id == project_id)
        .scalar()
    ) or 0

    # --- Komunitas ---
    community_agg = (
        db.query(
            func.sum(CommunityData.beneficiary_count).label("total_beneficiaries"),
            func.count(func.distinct(CommunityData.village_name)).label("total_villages"),
            func.sum(CommunityData.livelihood_groups).label("total_livelihood_groups"),
        )
        .filter(CommunityData.project_id == project_id)
        .first()
    )

    # --- Kegiatan Terbaru ---
    recent_activities_db = (
        db.query(ProjectActivity)
        .filter(ProjectActivity.project_id == project_id)
        .order_by(ProjectActivity.activity_date.desc())
        .limit(5)
        .all()
    )
    recent_activities = [
        {"id": a.id, "type": a.activity_type, "date": str(a.activity_date), "realization": a.realization, "unit": a.unit}
        for a in recent_activities_db
    ]

    # --- Alert Aktif ---
    active_alerts_db = (
        db.query(Alert)
        .filter(Alert.project_id == project_id, Alert.is_resolved == False)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )
    active_alerts_count = (
        db.query(func.count(Alert.id))
        .filter(Alert.project_id == project_id, Alert.is_resolved == False)
        .scalar()
    ) or 0
    recent_alerts = [
        {"id": a.id, "type": a.alert_type, "severity": a.severity, "description": a.description, "created_at": str(a.created_at)}
        for a in active_alerts_db
    ]

    # --- Field Reports ---
    total_field_reports = (
        db.query(func.count(FieldReport.id))
        .filter(FieldReport.project_id == project_id)
        .scalar()
    ) or 0
    last_field_report_obj = (
        db.query(FieldReport)
        .filter(FieldReport.project_id == project_id)
        .order_by(FieldReport.report_date.desc())
        .first()
    )

    return DashboardResponse(
        project_id=project.id,
        project_name=project.name,
        project_status=project.status,
        area_ha=project.area_ha,
        trees_planted=trees_planted,
        trees_survived=trees_survived,
        trees_dead=trees_dead,
        survival_rate=survival_rate,
        carbon_stock_tco2e=latest_carbon.carbon_stock_tco2e if latest_carbon else None,
        estimated_co2e=latest_carbon.estimated_co2e if latest_carbon else None,
        species_recorded=species_recorded,
        total_beneficiaries=int(community_agg.total_beneficiaries or 0),
        total_villages=int(community_agg.total_villages or 0),
        total_livelihood_groups=int(community_agg.total_livelihood_groups or 0),
        total_activities=len(recent_activities_db),
        recent_activities=recent_activities,
        active_alerts=active_alerts_count,
        recent_alerts=recent_alerts,
        total_field_reports=total_field_reports,
        last_field_report=last_field_report_obj.report_date if last_field_report_obj else None,
    )


# ─────────────────────────────────────────────
# PROJECT ACTIVITIES
# ─────────────────────────────────────────────

@router.post("/{project_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    project_id: int,
    body: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mencatat kegiatan proyek baru.

    Jenis kegiatan: `planting`, `restoration`, `biodiversity_survey`,
    `community_development`, `fire_prevention`, `forest_protection`.
    """
    require_admin(current_user)
    get_project_or_404(project_id, db)

    activity = ProjectActivity(
        project_id=project_id,
        activity_type=body.activity_type,
        activity_date=body.activity_date,
        location_geojson=body.location_geojson,
        target=body.target,
        realization=body.realization,
        unit=body.unit,
        executor=body.executor,
        photo_urls=body.photo_urls,
        notes=body.notes,
        created_by=current_user.id,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/{project_id}/activities", response_model=List[ActivityResponse])
def list_activities(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mendapatkan semua kegiatan untuk satu proyek, diurutkan dari terbaru."""
    get_project_or_404(project_id, db)
    return (
        db.query(ProjectActivity)
        .filter(ProjectActivity.project_id == project_id)
        .order_by(ProjectActivity.activity_date.desc())
        .all()
    )


@router.get("/{project_id}/activities/{activity_id}", response_model=ActivityResponse)
def get_activity(
    project_id: int,
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mendapatkan detail satu kegiatan."""
    get_project_or_404(project_id, db)
    activity = (
        db.query(ProjectActivity)
        .filter(ProjectActivity.id == activity_id, ProjectActivity.project_id == project_id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Kegiatan tidak ditemukan.")
    return activity


# ─────────────────────────────────────────────
# TREE RECORDS
# ─────────────────────────────────────────────

@router.post("/{project_id}/trees", response_model=TreeRecordResponse, status_code=status.HTTP_201_CREATED)
def create_tree_record(
    project_id: int,
    body: TreeRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menambahkan data tanam pohon (per batch/plot).

    Setelah data disimpan, sistem otomatis mengecek survival rate.
    Jika survival rate < 70%, alert `low_tree_survival` akan dibuat secara otomatis.
    """
    require_admin(current_user)
    get_project_or_404(project_id, db)

    record = TreeRecord(
        project_id=project_id,
        plot_id=body.plot_id,
        species=body.species,
        quantity=body.quantity,
        planting_date=body.planting_date,
        location_geojson=body.location_geojson,
        condition=body.condition or "healthy",
        height_cm=body.height_cm,
        dbh_cm=body.dbh_cm,
        is_alive=body.is_alive if body.is_alive is not None else True,
        photo_urls=body.photo_urls,
        notes=body.notes,
        last_monitored=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Auto-check survival rate setelah data baru ditambahkan
    check_and_create_survival_alert(db, project_id)

    return record


@router.get("/{project_id}/trees", response_model=List[TreeRecordResponse])
def list_tree_records(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mendapatkan semua record pohon untuk satu proyek."""
    get_project_or_404(project_id, db)
    return (
        db.query(TreeRecord)
        .filter(TreeRecord.project_id == project_id)
        .order_by(TreeRecord.planting_date.desc())
        .all()
    )


@router.get("/{project_id}/trees/summary", response_model=TreeSummary)
def get_tree_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ringkasan statistik pohon proyek:
    Trees Planted, Survived, Dead, dan Survival Rate (%).
    """
    get_project_or_404(project_id, db)
    records = db.query(TreeRecord).filter(TreeRecord.project_id == project_id).all()

    trees_planted = sum(r.quantity for r in records)
    trees_survived = sum(r.quantity for r in records if r.is_alive)
    trees_dead = trees_planted - trees_survived
    survival_rate = round((trees_survived / trees_planted * 100), 2) if trees_planted > 0 else 0.0
    alert_triggered = survival_rate < 70.0 and trees_planted > 0

    return TreeSummary(
        trees_planted=trees_planted,
        trees_survived=trees_survived,
        trees_dead=trees_dead,
        survival_rate=survival_rate,
        alert_triggered=alert_triggered,
    )


@router.put("/{project_id}/trees/{tree_id}", response_model=TreeRecordResponse)
def update_tree_record(
    project_id: int,
    tree_id: int,
    body: TreeRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update kondisi pohon (monitoring berkala).

    Setelah update, sistem otomatis mengecek survival rate dan membuat alert jika diperlukan.
    """
    require_admin(current_user)
    get_project_or_404(project_id, db)

    record = (
        db.query(TreeRecord)
        .filter(TreeRecord.id == tree_id, TreeRecord.project_id == project_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Data pohon tidak ditemukan.")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    record.last_monitored = datetime.utcnow()
    db.commit()
    db.refresh(record)

    # Auto-check survival rate setelah update
    check_and_create_survival_alert(db, project_id)

    return record


# ─────────────────────────────────────────────
# FIELD REPORTS
# ─────────────────────────────────────────────

@router.post("/{project_id}/field-reports", response_model=FieldReportResponse, status_code=status.HTTP_201_CREATED)
def create_field_report(
    project_id: int,
    body: FieldReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit laporan dari petugas lapangan.

    Setiap laporan mencakup: **WHO** (officer) + **WHERE** (GPS) +
    **WHEN** (tanggal) + **WHAT** (aktivitas) + **EVIDENCE** (foto).
    """
    get_project_or_404(project_id, db)

    report = FieldReport(
        project_id=project_id,
        officer_name=body.officer_name,
        plot_id=body.plot_id,
        location_geojson=body.location_geojson,
        report_date=body.report_date,
        report_type=body.report_type,
        activity_description=body.activity_description,
        result_description=body.result_description,
        photo_urls=body.photo_urls,
        created_by=current_user.id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/{project_id}/field-reports", response_model=List[FieldReportResponse])
def list_field_reports(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mendapatkan semua laporan lapangan untuk satu proyek."""
    get_project_or_404(project_id, db)
    return (
        db.query(FieldReport)
        .filter(FieldReport.project_id == project_id)
        .order_by(FieldReport.report_date.desc())
        .all()
    )


@router.get("/{project_id}/field-reports/{report_id}", response_model=FieldReportResponse)
def get_field_report(
    project_id: int,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mendapatkan detail satu laporan lapangan."""
    get_project_or_404(project_id, db)
    report = (
        db.query(FieldReport)
        .filter(FieldReport.id == report_id, FieldReport.project_id == project_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan.")
    return report


# ─────────────────────────────────────────────
# ALERTS
# ─────────────────────────────────────────────

@router.get("/{project_id}/alerts", response_model=List[AlertResponse])
def list_alerts(
    project_id: int,
    only_active: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mendapatkan daftar alert untuk satu proyek.

    - `only_active=true` (default): Hanya alert yang belum resolved.
    - `only_active=false`: Semua alert termasuk yang sudah resolved.

    Endpoint ini juga men-trigger auto-check monitoring_overdue.
    """
    get_project_or_404(project_id, db)

    # Auto-check monitoring overdue setiap kali alert di-fetch
    check_and_create_overdue_alert(db, project_id)

    query = db.query(Alert).filter(Alert.project_id == project_id)
    if only_active:
        query = query.filter(Alert.is_resolved == False)

    return query.order_by(Alert.created_at.desc()).all()


@router.post("/{project_id}/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    project_id: int,
    body: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Membuat alert secara manual oleh admin.

    Tipe alert yang tersedia: `deforestation`, `fire`, `land_cover_change`,
    `monitoring_overdue`, `low_tree_survival`.
    """
    require_admin(current_user)
    get_project_or_404(project_id, db)

    alert = Alert(
        project_id=project_id,
        alert_type=body.alert_type,
        severity=body.severity or "medium",
        location_geojson=body.location_geojson,
        description=body.description,
        auto_generated=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.put("/{project_id}/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    project_id: int,
    alert_id: int,
    body: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update status alert: mark as read atau mark as resolved.

    Ketika `is_resolved` diset ke `true`, `resolved_at` otomatis diisi dengan waktu sekarang.
    """
    get_project_or_404(project_id, db)
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.project_id == project_id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert tidak ditemukan.")

    if body.is_read is not None:
        alert.is_read = body.is_read
    if body.is_resolved is not None:
        alert.is_resolved = body.is_resolved
        if body.is_resolved and not alert.resolved_at:
            alert.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)
    return alert


# ─────────────────────────────────────────────
# BIODIVERSITY OBSERVATIONS
# ─────────────────────────────────────────────

@router.post("/{project_id}/biodiversity", response_model=BiodiversityResponse, status_code=status.HTTP_201_CREATED)
def create_biodiversity_observation(
    project_id: int,
    body: BiodiversityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mencatat observasi biodiversitas baru (satwa atau flora)."""
    require_admin(current_user)
    get_project_or_404(project_id, db)

    obs = BiodiversityObservation(
        project_id=project_id,
        species_name=body.species_name,
        species_type=body.species_type,
        location_geojson=body.location_geojson,
        observed_date=body.observed_date,
        habitat=body.habitat,
        observer=body.observer,
        photo_url=body.photo_url,
        notes=body.notes,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.get("/{project_id}/biodiversity", response_model=List[BiodiversityResponse])
def list_biodiversity_observations(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mendapatkan semua observasi biodiversitas untuk satu proyek."""
    get_project_or_404(project_id, db)
    return (
        db.query(BiodiversityObservation)
        .filter(BiodiversityObservation.project_id == project_id)
        .order_by(BiodiversityObservation.observed_date.desc())
        .all()
    )


@router.get("/{project_id}/biodiversity/summary", response_model=BiodiversitySummary)
def get_biodiversity_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ringkasan biodiversitas: jumlah total observasi, spesies unik, fauna, dan flora."""
    get_project_or_404(project_id, db)
    all_obs = db.query(BiodiversityObservation).filter(
        BiodiversityObservation.project_id == project_id
    ).all()

    unique_species = len(set(o.species_name for o in all_obs))
    fauna_count = sum(1 for o in all_obs if o.species_type == "fauna")
    flora_count = sum(1 for o in all_obs if o.species_type == "flora")

    return BiodiversitySummary(
        total_observations=len(all_obs),
        unique_species=unique_species,
        fauna_count=fauna_count,
        flora_count=flora_count,
    )


# ─────────────────────────────────────────────
# COMMUNITY DATA
# ─────────────────────────────────────────────

@router.post("/{project_id}/community", response_model=CommunityResponse, status_code=status.HTTP_201_CREATED)
def create_community_data(
    project_id: int,
    body: CommunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mencatat data dampak sosial dan ekonomi proyek terhadap komunitas."""
    require_admin(current_user)
    get_project_or_404(project_id, db)

    data = CommunityData(
        project_id=project_id,
        village_name=body.village_name,
        beneficiary_count=body.beneficiary_count or 0,
        livelihood_groups=body.livelihood_groups or 0,
        employment_count=body.employment_count or 0,
        community_investment=body.community_investment or 0.0,
        activity_type=body.activity_type,
        description=body.description,
        date=body.date,
    )
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/{project_id}/community", response_model=List[CommunityResponse])
def list_community_data(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mendapatkan semua data komunitas untuk satu proyek."""
    get_project_or_404(project_id, db)
    return (
        db.query(CommunityData)
        .filter(CommunityData.project_id == project_id)
        .order_by(CommunityData.created_at.desc())
        .all()
    )


@router.get("/{project_id}/community/summary", response_model=CommunitySummary)
def get_community_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ringkasan dampak komunitas: villages, beneficiaries, livelihood groups, employment."""
    get_project_or_404(project_id, db)
    all_data = db.query(CommunityData).filter(CommunityData.project_id == project_id).all()

    return CommunitySummary(
        total_villages=len(set(d.village_name for d in all_data)),
        total_beneficiaries=sum(d.beneficiary_count for d in all_data),
        total_livelihood_groups=sum(d.livelihood_groups for d in all_data),
        total_employment=sum(d.employment_count for d in all_data),
        total_community_investment=sum(d.community_investment for d in all_data),
    )


# ─────────────────────────────────────────────
# CARBON RECORDS
# ─────────────────────────────────────────────

@router.post("/{project_id}/carbon", response_model=CarbonResponse, status_code=status.HTTP_201_CREATED)
def create_carbon_record(
    project_id: int,
    body: CarbonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menambahkan data monitoring karbon untuk satu periode.

    **Penting**: Data ini adalah estimasi monitoring, bukan verified carbon credit.
    """
    require_admin(current_user)
    get_project_or_404(project_id, db)

    record = CarbonRecord(
        project_id=project_id,
        period_start=body.period_start,
        period_end=body.period_end,
        carbon_stock_tco2e=body.carbon_stock_tco2e,
        biomass_ton=body.biomass_ton,
        estimated_co2e=body.estimated_co2e,
        carbon_change=body.carbon_change,
        methodology=body.methodology,
        notes=body.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{project_id}/carbon", response_model=List[CarbonResponse])
def list_carbon_records(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mendapatkan semua record karbon untuk satu proyek, diurutkan dari periode terbaru."""
    get_project_or_404(project_id, db)
    return (
        db.query(CarbonRecord)
        .filter(CarbonRecord.project_id == project_id)
        .order_by(CarbonRecord.period_end.desc())
        .all()
    )

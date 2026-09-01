"""
services/alert_service.py — Mesin Evaluasi Alert Otomatis SATUBUMI MONITOR

Mengevaluasi 5 Aturan Peringatan Dini Lingkungan:
1. Deforestation Alert (Kehilangan tutupan hutan > threshold ha)
2. Fire Alert (Terdeteksi titik api / burned area)
3. Land Cover Change (Penurunan drastis indeks vegetasi NDVI < 0.35)
4. Low Tree Survival Rate (Tingkat kelangsungan hidup pohon < 70%)
5. Monitoring Overdue (Tidak ada laporan lapangan / monitoring > 30 hari)
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional

from app.models.project import Project
from app.models.monitor import TreeRecord, FieldReport, Alert, LandscapeSnapshot

# Threshold Konfigurasi
SURVIVAL_RATE_THRESHOLD = 70.0     # Alert jika survival rate < 70%
MONITORING_OVERDUE_DAYS = 30       # Alert jika tidak ada field report > 30 hari
DEFORESTATION_THRESHOLD_HA = 0.5   # Alert jika deforestasi > 0.5 ha
NDVI_CRITICAL_THRESHOLD = 0.35     # Alert jika NDVI < 0.35


def check_and_create_survival_alert(db: Session, project_id: int) -> bool:
    """
    Cek survival rate pohon untuk satu proyek.
    Jika survival rate < SURVIVAL_RATE_THRESHOLD dan belum ada alert aktif, buat alert baru.
    """
    all_records = db.query(TreeRecord).filter(TreeRecord.project_id == project_id).all()
    if not all_records:
        return False

    total_planted = sum(r.quantity for r in all_records)
    total_survived = sum(r.quantity for r in all_records if r.is_alive)

    if total_planted == 0:
        return False

    survival_rate = (total_survived / total_planted) * 100

    if survival_rate >= SURVIVAL_RATE_THRESHOLD:
        return False

    # Cek apakah sudah ada alert low_tree_survival yang belum resolved
    existing_alert = (
        db.query(Alert)
        .filter(
            Alert.project_id == project_id,
            Alert.alert_type == "low_tree_survival",
            Alert.is_resolved == False,
        )
        .first()
    )
    if existing_alert:
        return False

    severity = "critical" if survival_rate < 50 else "high"
    alert = Alert(
        project_id=project_id,
        alert_type="low_tree_survival",
        severity=severity,
        description=(
            f"Survival rate pohon turun ke {survival_rate:.1f}% "
            f"({total_survived:,} dari {total_planted:,} pohon masih hidup). "
            f"Threshold minimum: {SURVIVAL_RATE_THRESHOLD}%."
        ),
        auto_generated=True,
    )
    db.add(alert)
    db.commit()
    return True


def check_and_create_overdue_alert(db: Session, project_id: int) -> bool:
    """
    Cek apakah proyek sudah terlalu lama tidak ada field report (> 30 hari).
    """
    last_report = (
        db.query(FieldReport)
        .filter(FieldReport.project_id == project_id)
        .order_by(FieldReport.report_date.desc())
        .first()
    )

    is_overdue = (
        last_report is None
        or (datetime.utcnow() - last_report.report_date) > timedelta(days=MONITORING_OVERDUE_DAYS)
    )

    if not is_overdue:
        return False

    existing_alert = (
        db.query(Alert)
        .filter(
            Alert.project_id == project_id,
            Alert.alert_type == "monitoring_overdue",
            Alert.is_resolved == False,
        )
        .first()
    )
    if existing_alert:
        return False

    if last_report is None:
        description = "Proyek belum memiliki field report sama sekali. Segera lakukan monitoring lapangan."
    else:
        days_ago = (datetime.utcnow() - last_report.report_date).days
        description = (
            f"Field report terakhir dilakukan {days_ago} hari lalu "
            f"(lebih dari {MONITORING_OVERDUE_DAYS} hari). Segera lakukan monitoring lapangan."
        )

    alert = Alert(
        project_id=project_id,
        alert_type="monitoring_overdue",
        severity="medium",
        description=description,
        auto_generated=True,
    )
    db.add(alert)
    db.commit()
    return True


def check_deforestation_alert(db: Session, project: Project) -> bool:
    """
    Cek indikasi kehilangan tutupan hutan dari snapshot remote sensing terakhir.
    """
    latest_snapshot = (
        db.query(LandscapeSnapshot)
        .filter(LandscapeSnapshot.project_id == project.id)
        .order_by(LandscapeSnapshot.snapshot_date.desc())
        .first()
    )
    if not latest_snapshot or not latest_snapshot.deforestation_ha:
        return False

    if latest_snapshot.deforestation_ha <= DEFORESTATION_THRESHOLD_HA:
        return False

    existing_alert = (
        db.query(Alert)
        .filter(
            Alert.project_id == project.id,
            Alert.alert_type == "deforestation",
            Alert.is_resolved == False,
        )
        .first()
    )
    if existing_alert:
        return False

    alert = Alert(
        project_id=project.id,
        alert_type="deforestation",
        severity="high",
        location_geojson=project.boundary_geojson,
        description=f"Peringatan Deforestasi: Terdeteksi kehilangan tutupan hutan seluas {latest_snapshot.deforestation_ha} ha pada snapshot {latest_snapshot.snapshot_date.isoformat()}.",
        auto_generated=True,
        source_url="https://earthengine.google.com",
    )
    db.add(alert)
    db.commit()
    return True


def check_fire_alert(db: Session, project: Project) -> bool:
    """
    Cek indikasi titik api / burned area dari snapshot telemetri satelit terakhir.
    """
    latest_snapshot = (
        db.query(LandscapeSnapshot)
        .filter(LandscapeSnapshot.project_id == project.id)
        .order_by(LandscapeSnapshot.snapshot_date.desc())
        .first()
    )
    if not latest_snapshot or not latest_snapshot.fire_ha:
        return False

    if latest_snapshot.fire_ha <= 0.0:
        return False

    existing_alert = (
        db.query(Alert)
        .filter(
            Alert.project_id == project.id,
            Alert.alert_type == "fire",
            Alert.is_resolved == False,
        )
        .first()
    )
    if existing_alert:
        return False

    alert = Alert(
        project_id=project.id,
        alert_type="fire",
        severity="critical",
        location_geojson=project.boundary_geojson,
        description=f"Peringatan Titik Api: Terdeteksi area terbakar seluas {latest_snapshot.fire_ha} ha pada {latest_snapshot.snapshot_date.isoformat()}.",
        auto_generated=True,
        source_url="https://firms.modaps.eosdis.nasa.gov",
    )
    db.add(alert)
    db.commit()
    return True


def check_land_cover_degradation_alert(db: Session, project: Project) -> bool:
    """
    Cek indikasi penurunan drastis NDVI vegetasi tajuk pohon.
    """
    latest_snapshot = (
        db.query(LandscapeSnapshot)
        .filter(LandscapeSnapshot.project_id == project.id)
        .order_by(LandscapeSnapshot.snapshot_date.desc())
        .first()
    )
    if not latest_snapshot or latest_snapshot.ndvi_mean is None:
        return False

    if latest_snapshot.ndvi_mean >= NDVI_CRITICAL_THRESHOLD:
        return False

    existing_alert = (
        db.query(Alert)
        .filter(
            Alert.project_id == project.id,
            Alert.alert_type == "land_cover_change",
            Alert.is_resolved == False,
        )
        .first()
    )
    if existing_alert:
        return False

    alert = Alert(
        project_id=project.id,
        alert_type="land_cover_change",
        severity="medium",
        location_geojson=project.boundary_geojson,
        description=f"Peringatan Penurunan NDVI: Rata-rata indeks vegetasi turun ke {latest_snapshot.ndvi_mean} (di bawah ambang {NDVI_CRITICAL_THRESHOLD}).",
        auto_generated=True,
        source_url="https://earthengine.google.com",
    )
    db.add(alert)
    db.commit()
    return True


def check_all_project_alerts(db: Session, project: Project) -> Dict[str, Any]:
    """
    Menjalankan seluruh evaluasi aturan alert otomatis secara serentak.
    """
    new_alerts = []

    if check_and_create_survival_alert(db, project.id):
        new_alerts.append("low_tree_survival")

    if check_and_create_overdue_alert(db, project.id):
        new_alerts.append("monitoring_overdue")

    if check_deforestation_alert(db, project):
        new_alerts.append("deforestation")

    if check_fire_alert(db, project):
        new_alerts.append("fire")

    if check_land_cover_degradation_alert(db, project):
        new_alerts.append("land_cover_change")

    total_active = (
        db.query(func.count(Alert.id))
        .filter(Alert.project_id == project.id, Alert.is_resolved == False)
        .scalar()
    ) or 0

    return {
        "project_id": project.id,
        "evaluated_rules": 5,
        "new_alerts_created": new_alerts,
        "total_active_alerts": total_active,
        "message": f"Evaluasi 5 aturan alert selesai. {len(new_alerts)} alert baru dibuat." if new_alerts else "Evaluasi selesai. Tidak ada anomali atau alert baru yang dipicu."
    }


def get_alerts_summary(db: Session, project_id: int) -> Dict[str, Any]:
    """
    Menghitung ringkasan statistik alert proyek (kategori, severity, status resolved).
    """
    all_alerts = db.query(Alert).filter(Alert.project_id == project_id).all()

    total_alerts = len(all_alerts)
    active_alerts = sum(1 for a in all_alerts if not a.is_resolved)
    resolved_alerts = sum(1 for a in all_alerts if a.is_resolved)
    res_rate = round((resolved_alerts / total_alerts * 100), 1) if total_alerts > 0 else 100.0

    by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_type = {
        "deforestation": 0,
        "fire": 0,
        "land_cover_change": 0,
        "monitoring_overdue": 0,
        "low_tree_survival": 0
    }

    for a in all_alerts:
        sev = a.severity.lower() if a.severity else "medium"
        if sev in by_sev:
            by_sev[sev] += 1

        atype = a.alert_type.lower() if a.alert_type else "general"
        if atype in by_type:
            by_type[atype] += 1
        else:
            by_type[atype] = 1

    latest_alerts = (
        db.query(Alert)
        .filter(Alert.project_id == project_id)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "project_id": project_id,
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "resolved_alerts": resolved_alerts,
        "resolution_rate_pct": res_rate,
        "by_severity": by_sev,
        "by_type": by_type,
        "latest_alerts": latest_alerts,
    }

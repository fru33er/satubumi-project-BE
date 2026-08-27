"""
Alert Service — Logika auto-trigger untuk sistem alert SATUBUMI MONITOR.

Digunakan oleh router monitor.py untuk mengecek kondisi dan membuat alert
secara otomatis tanpa perlu Celery/background worker.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.monitor import Alert, FieldReport, TreeRecord

# Threshold untuk auto-alert
SURVIVAL_RATE_THRESHOLD = 70.0  # Alert jika survival rate < 70%
MONITORING_OVERDUE_DAYS = 30  # Alert jika tidak ada field report > 30 hari


def check_and_create_survival_alert(db: Session, project_id: int) -> bool:
    """
    Cek survival rate pohon untuk satu proyek.
    Jika survival rate < SURVIVAL_RATE_THRESHOLD dan belum ada alert aktif,
    buat alert baru secara otomatis.

    Returns:
        bool: True jika alert baru dibuat, False jika tidak.
    """
    # Hitung total dan yang masih hidup
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

    # Buat alert baru
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
    Cek apakah proyek sudah terlalu lama tidak ada field report.
    Jika last field report > MONITORING_OVERDUE_DAYS hari lalu (atau belum ada sama sekali),
    buat alert monitoring_overdue secara otomatis.

    Returns:
        bool: True jika alert baru dibuat, False jika tidak.
    """
    last_report = (
        db.query(FieldReport)
        .filter(FieldReport.project_id == project_id)
        .order_by(FieldReport.report_date.desc())
        .first()
    )

    is_overdue = last_report is None or (
        datetime.utcnow() - last_report.report_date
    ) > timedelta(days=MONITORING_OVERDUE_DAYS)

    if not is_overdue:
        return False

    # Cek apakah sudah ada alert monitoring_overdue yang belum resolved
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

    # Tentukan pesan
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

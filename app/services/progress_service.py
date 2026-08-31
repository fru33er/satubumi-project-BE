"""
services/progress_service.py — Kalkulasi Target vs Actual untuk Proyek

Logic:
- Membaca targets_json dari proyek
- Menghitung realisasi dari data aktual (tree_records, project_activities)
- Return persentase progress per key target

Key target yang didukung:
  - "tree_planting"    → sum(tree_records.quantity)
  - "restoration_ha"  → sum(activities.realization where type=restoration)
  - "planting_ha"     → sum(activities.realization where type=planting)
  - "protection_ha"   → sum(activities.realization where type=forest_protection)
  - "community_ha"    → sum(activities.realization where type=community_development)
  - Key lain          → fallback ke sum(activities.realization where type=key)
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, Optional
from app.models.project import Project
from app.models.monitor import TreeRecord, ProjectActivity


# Mapping antara target key dan activity_type di project_activities
TARGET_TO_ACTIVITY_TYPE: Dict[str, str] = {
    "restoration_ha": "restoration",
    "planting_ha": "planting",
    "protection_ha": "forest_protection",
    "community_ha": "community_development",
    "fire_prevention_ha": "fire_prevention",
    "biodiversity_survey": "biodiversity_survey",
}


def calculate_project_progress(db: Session, project: Project) -> Dict[str, Any]:
    """
    Menghitung progress Target vs Actual untuk sebuah proyek.

    Args:
        db: Database session
        project: Project model instance

    Returns:
        Dict berisi:
        - targets: Dict per target key {target, actual, progress_pct, unit}
        - tree_summary: Ringkasan pohon {planted, survived, dead, survival_rate}
        - activities_by_type: Ringkasan kegiatan per type {count, total_realization, unit}
        - overall_progress_pct: Rata-rata progress semua target (jika ada)
    """
    targets_json: Dict[str, Any] = project.targets_json or {}
    project_id = project.id

    # ── 1. Hitung aktual dari tree_records ───────────────────────────────────
    tree_stats = _get_tree_stats(db, project_id)

    # ── 2. Hitung aktual dari project_activities ─────────────────────────────
    activity_stats = _get_activity_stats(db, project_id)

    # ── 3. Kalkulasi progress per target key ─────────────────────────────────
    targets_result: Dict[str, Any] = {}
    progress_values = []

    for key, target_val in targets_json.items():
        if target_val is None or target_val == 0:
            continue

        actual_val = _resolve_actual(
            key=key,
            tree_stats=tree_stats,
            activity_stats=activity_stats,
        )
        progress_pct = round((actual_val / target_val) * 100, 1) if target_val > 0 else 0.0
        unit = _get_unit_for_key(key)

        targets_result[key] = {
            "target": target_val,
            "actual": actual_val,
            "progress_pct": min(progress_pct, 100.0),  # Cap at 100%
            "unit": unit,
        }
        progress_values.append(min(progress_pct, 100.0))

    overall_pct = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0.0

    return {
        "project_id": project_id,
        "project_name": project.name,
        "targets": targets_result,
        "tree_summary": tree_stats,
        "activities_by_type": activity_stats,
        "overall_progress_pct": overall_pct,
    }


# ── Private Helpers ───────────────────────────────────────────────────────────

def _get_tree_stats(db: Session, project_id: int) -> Dict[str, Any]:
    """Agregasi statistik pohon dari tree_records."""
    from sqlalchemy import case

    rows = db.query(TreeRecord).filter(TreeRecord.project_id == project_id).all()

    total_planted = sum(r.quantity for r in rows)
    total_alive = sum(r.quantity for r in rows if r.is_alive)
    total_dead = total_planted - total_alive
    survival_rate = round((total_alive / total_planted) * 100, 1) if total_planted > 0 else 0.0

    return {
        "planted": total_planted,
        "survived": total_alive,
        "dead": total_dead,
        "survival_rate": survival_rate,
        "total_batches": len(rows),
    }


def _get_activity_stats(db: Session, project_id: int) -> Dict[str, Any]:
    """Agregasi kegiatan per activity_type."""
    rows = db.query(ProjectActivity).filter(ProjectActivity.project_id == project_id).all()

    stats: Dict[str, Any] = {}
    for activity in rows:
        atype = activity.activity_type
        if atype not in stats:
            stats[atype] = {"count": 0, "total_realization": 0.0, "unit": activity.unit}
        stats[atype]["count"] += 1
        stats[atype]["total_realization"] += activity.realization or 0.0

    return stats


def _resolve_actual(
    key: str,
    tree_stats: Dict[str, Any],
    activity_stats: Dict[str, Any],
) -> float:
    """Resolve nilai aktual untuk sebuah target key."""
    # Key khusus tree_planting → dari tree_records.quantity
    if key == "tree_planting":
        return float(tree_stats.get("planted", 0))

    # Key yang mapping ke activity_type
    activity_type = TARGET_TO_ACTIVITY_TYPE.get(key, key)
    if activity_type in activity_stats:
        return float(activity_stats[activity_type].get("total_realization", 0.0))

    # Fallback: coba cocokkan key langsung ke activity_type
    if key in activity_stats:
        return float(activity_stats[key].get("total_realization", 0.0))

    return 0.0


def _get_unit_for_key(key: str) -> str:
    """Return unit label untuk sebuah target key."""
    units = {
        "tree_planting": "pohon",
        "restoration_ha": "ha",
        "planting_ha": "ha",
        "protection_ha": "ha",
        "community_ha": "ha",
        "fire_prevention_ha": "ha",
        "biodiversity_survey": "kegiatan",
    }
    return units.get(key, "unit")

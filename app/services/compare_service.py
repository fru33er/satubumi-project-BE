"""
services/compare_service.py — Comparison Engine untuk SATUBUMI MONITOR

Menyediakan dua mode komparasi performa:
1. Baseline vs Current Comparison: Membandingkan metrik proyek saat ini terhadap kondisi awal tanam (Baseline).
2. Multi-Project Comparison Matrix: Membandingkan beberapa proyek secara berdampingan dengan benchmarking.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import date

from app.models.project import Project
from app.models.monitor import (
    TreeRecord, TreeMeasurement, LandscapeSnapshot, CarbonRecord,
    BiodiversityObservation, Alert
)
from app.schemas.monitor import (
    BaselineComparisonMetric, ProjectBaselineComparisonResponse,
    ProjectComparisonCard, MultiProjectComparisonResponse
)
from app.services.progress_service import calculate_project_progress


def compare_project_with_baseline(db: Session, project: Project) -> ProjectBaselineComparisonResponse:
    """
    Membandingkan metrik kondisi saat ini (Current) terhadap kondisi dasar awal tanam (Baseline).
    """
    today = date.today()

    # Tentukan baseline date: tanggal tanam pohon terawal atau tanggal mulai proyek
    earliest_tree = (
        db.query(TreeRecord)
        .filter(TreeRecord.project_id == project.id)
        .order_by(TreeRecord.planting_date.asc())
        .first()
    )
    baseline_date = earliest_tree.planting_date if earliest_tree else project.start_date

    metrics: List[BaselineComparisonMetric] = []

    # 1. Metrik: Tutupan Hutan (Forest Cover)
    snapshots = (
        db.query(LandscapeSnapshot)
        .filter(LandscapeSnapshot.project_id == project.id)
        .order_by(LandscapeSnapshot.snapshot_date.asc())
        .all()
    )
    if snapshots:
        first_snap = snapshots[0]
        latest_snap = snapshots[-1]
        b_val = first_snap.forest_cover_ha or 0.0
        c_val = latest_snap.forest_cover_ha or 0.0
        diff = round(c_val - b_val, 2)
        pct = round((diff / b_val * 100), 1) if b_val > 0 else 0.0
        metrics.append(BaselineComparisonMetric(
            metric_name="Tutupan Hutan (Forest Cover)",
            unit="ha",
            baseline_value=b_val,
            current_value=c_val,
            change_value=diff,
            change_pct=pct,
            status="improved" if diff >= 0 else "declined"
        ))

        # 2. Metrik: Indeks Vegetasi (NDVI)
        b_ndvi = first_snap.ndvi_mean or 0.50
        c_ndvi = latest_snap.ndvi_mean or 0.50
        diff_ndvi = round(c_ndvi - b_ndvi, 3)
        pct_ndvi = round((diff_ndvi / b_ndvi * 100), 1) if b_ndvi > 0 else 0.0
        metrics.append(BaselineComparisonMetric(
            metric_name="Indeks Vegetasi (NDVI)",
            unit="index",
            baseline_value=round(b_ndvi, 3),
            current_value=round(c_ndvi, 3),
            change_value=diff_ndvi,
            change_pct=pct_ndvi,
            status="improved" if diff_ndvi >= 0 else "declined"
        ))

    # 3. Metrik: Tinggi Rata-rata Pohon (Average Height)
    all_trees = db.query(TreeRecord).filter(TreeRecord.project_id == project.id).all()
    measurements = db.query(TreeMeasurement).filter(TreeMeasurement.project_id == project.id).all()

    if all_trees:
        baseline_heights = [t.height_cm for t in all_trees if t.height_cm is not None]
        b_h = round(sum(baseline_heights) / len(baseline_heights), 1) if baseline_heights else None

        current_heights = []
        for t in all_trees:
            t_m = [m for m in measurements if m.tree_record_id == t.id and m.height_cm is not None]
            if t_m:
                latest_m = max(t_m, key=lambda x: x.measurement_date)
                current_heights.append(latest_m.height_cm)
            elif t.height_cm is not None:
                current_heights.append(t.height_cm)

        c_h = round(sum(current_heights) / len(current_heights), 1) if current_heights else None

        if b_h is not None and c_h is not None:
            diff_h = round(c_h - b_h, 1)
            pct_h = round((diff_h / b_h * 100), 1) if b_h > 0 else 0.0
            metrics.append(BaselineComparisonMetric(
                metric_name="Rata-rata Tinggi Pohon",
                unit="cm",
                baseline_value=b_h,
                current_value=c_h,
                change_value=diff_h,
                change_pct=pct_h,
                status="improved" if diff_h >= 0 else "declined"
            ))

    # 4. Metrik: Estimasi Cadangan Karbon (Carbon Stock)
    carbons = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.project_id == project.id)
        .order_by(CarbonRecord.period_start.asc())
        .all()
    )
    if carbons:
        b_c = carbons[0].carbon_stock_tco2e or 0.0
        c_c = carbons[-1].carbon_stock_tco2e or 0.0
        diff_c = round(c_c - b_c, 2)
        pct_c = round((diff_c / b_c * 100), 1) if b_c > 0 else 0.0
        metrics.append(BaselineComparisonMetric(
            metric_name="Cadangan Karbon (Carbon Stock)",
            unit="tCO2e",
            baseline_value=b_c,
            current_value=c_c,
            change_value=diff_c,
            change_pct=pct_c,
            status="improved" if diff_c >= 0 else "declined"
        ))

    # 5. Metrik: Keragaman Spesies (Species Richness)
    unique_species_count = (
        db.query(func.count(func.distinct(BiodiversityObservation.species_name)))
        .filter(BiodiversityObservation.project_id == project.id)
        .scalar()
    ) or 0
    metrics.append(BaselineComparisonMetric(
        metric_name="Keragaman Spesies Tercatat",
        unit="spesies",
        baseline_value=0.0,
        current_value=float(unique_species_count),
        change_value=float(unique_species_count),
        change_pct=100.0 if unique_species_count > 0 else 0.0,
        status="improved" if unique_species_count > 0 else "stable"
    ))

    narrative = f"Sejak baseline ({baseline_date.isoformat() if baseline_date else 'Awal Proyek'}), proyek '{project.name}' mencatatkan peningkatan pada {sum(1 for m in metrics if m.status == 'improved')} dari {len(metrics)} indikator utama."

    return ProjectBaselineComparisonResponse(
        project_id=project.id,
        project_name=project.name,
        baseline_date=baseline_date,
        current_date=today,
        metrics=metrics,
        summary_narrative=narrative,
    )


def compare_multiple_projects(db: Session, project_ids: List[int]) -> MultiProjectComparisonResponse:
    """
    Membandingkan sejumlah proyek sekaligus dan menghasilkan kartu komparasi matriks serta benchmark leader.
    """
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    cards: List[ProjectComparisonCard] = []

    for p in projects:
        progress_info = calculate_project_progress(db, p)
        tree_summary = progress_info.get("tree_summary", {})
        planted = tree_summary.get("planted", 0)
        survival = tree_summary.get("survival_rate", 0.0)

        latest_carbon = (
            db.query(CarbonRecord)
            .filter(CarbonRecord.project_id == p.id)
            .order_by(CarbonRecord.period_end.desc())
            .first()
        )
        carbon_stock = latest_carbon.carbon_stock_tco2e if latest_carbon else None

        species_count = (
            db.query(func.count(func.distinct(BiodiversityObservation.species_name)))
            .filter(BiodiversityObservation.project_id == p.id)
            .scalar()
        ) or 0

        active_alerts = (
            db.query(func.count(Alert.id))
            .filter(Alert.project_id == p.id, Alert.is_resolved == False)
            .scalar()
        ) or 0

        cards.append(ProjectComparisonCard(
            project_id=p.id,
            name=p.name,
            location_name=p.location_name,
            project_type=p.project_type,
            area_ha=p.area_ha,
            status=p.status,
            overall_progress_pct=progress_info.get("overall_progress_pct", 0.0),
            trees_planted=planted,
            survival_rate_pct=survival,
            carbon_stock_tco2e=carbon_stock,
            species_recorded=species_count,
            active_alerts_count=active_alerts,
        ))

    # Calculate Benchmark Leaders
    benchmarks: Dict[str, Any] = {}
    if cards:
        highest_survival = max(cards, key=lambda x: x.survival_rate_pct)
        highest_progress = max(cards, key=lambda x: x.overall_progress_pct)
        highest_planted = max(cards, key=lambda x: x.trees_planted)
        highest_biodiversity = max(cards, key=lambda x: x.species_recorded)

        benchmarks = {
            "highest_tree_survival": {
                "project_id": highest_survival.project_id,
                "project_name": highest_survival.name,
                "value": f"{highest_survival.survival_rate_pct}%",
            },
            "highest_overall_progress": {
                "project_id": highest_progress.project_id,
                "project_name": highest_progress.name,
                "value": f"{highest_progress.overall_progress_pct}%",
            },
            "most_trees_planted": {
                "project_id": highest_planted.project_id,
                "project_name": highest_planted.name,
                "value": f"{highest_planted.trees_planted} pohon",
            },
            "highest_species_richness": {
                "project_id": highest_biodiversity.project_id,
                "project_name": highest_biodiversity.name,
                "value": f"{highest_biodiversity.species_recorded} spesies",
            },
        }

    return MultiProjectComparisonResponse(
        total_projects=len(cards),
        projects=cards,
        benchmarks=benchmarks,
    )

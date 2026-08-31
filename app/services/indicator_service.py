"""
services/indicator_service.py — Indikator Kesehatan & Performa SATUBUMI MONITOR

Menghitung indikator ekologis dan sosial komprehensif:
1. Vegetation Health Index (NDVI)
2. Tree Performance & Survival Rate
3. Carbon Stock & Density
4. Biodiversity Richness Index
5. Community Impact Reach
6. Composite Project Health Score (0 - 100)
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.project import Project
from app.models.monitor import (
    TreeRecord, TreeMeasurement, LandscapeSnapshot, CarbonRecord,
    BiodiversityObservation, CommunityData, Alert
)
from app.schemas.monitor import (
    VegetationHealthIndicator, TreePerformanceIndicator, CarbonIndicator,
    BiodiversityIndicator, CommunityIndicator, ProjectIndicatorsResponse
)


def calculate_project_indicators(db: Session, project: Project) -> ProjectIndicatorsResponse:
    """
    Menghitung seluruh indikator kesehatan dan performa untuk sebuah proyek.
    """
    # ── 1. Vegetation Health (NDVI) ──
    latest_snapshot = (
        db.query(LandscapeSnapshot)
        .filter(LandscapeSnapshot.project_id == project.id)
        .order_by(LandscapeSnapshot.snapshot_date.desc())
        .first()
    )

    ndvi_val = latest_snapshot.ndvi_mean if (latest_snapshot and latest_snapshot.ndvi_mean is not None) else 0.65

    if ndvi_val >= 0.70:
        veg_status = "Sangat Baik"
        veg_desc = "Kerapatan dan kehijauan kanopi vegetasi sangat lebat dan sehat."
        veg_score = 95.0
    elif ndvi_val >= 0.50:
        veg_status = "Baik"
        veg_desc = "Tutupan vegetasi sehat dan stabil dengan sedikit area terbuka."
        veg_score = 80.0
    elif ndvi_val >= 0.35:
        veg_status = "Sedang"
        veg_desc = "Kerapatan vegetasi sedang, terdapat indikasi regenerasi lambat atau lahan terbuka."
        veg_score = 60.0
    else:
        veg_status = "Kritis"
        veg_desc = "Indeks vegetasi rendah, terindikasi degradasi lahan atau stres tajuk pohon berat."
        veg_score = 30.0

    veg_indicator = VegetationHealthIndicator(
        ndvi_mean=round(ndvi_val, 3),
        status=veg_status,
        description=veg_desc,
    )

    # ── 2. Tree Performance & Growth ──
    trees = db.query(TreeRecord).filter(TreeRecord.project_id == project.id).all()
    total_planted = sum(t.quantity for t in trees)
    total_survived = sum(t.quantity for t in trees if t.is_alive)
    survival_rate = round((total_survived / total_planted * 100), 1) if total_planted > 0 else 0.0

    # Calculate average growth delta across measured trees
    measurements = db.query(TreeMeasurement).filter(TreeMeasurement.project_id == project.id).all()
    height_deltas = []
    dbh_deltas = []

    for t in trees:
        t_measurements = [m for m in measurements if m.tree_record_id == t.id]
        if t_measurements and t.height_cm is not None:
            latest_m = max(t_measurements, key=lambda x: x.measurement_date)
            if latest_m.height_cm is not None:
                height_deltas.append(latest_m.height_cm - t.height_cm)
            if latest_m.dbh_cm is not None and t.dbh_cm is not None:
                dbh_deltas.append(latest_m.dbh_cm - t.dbh_cm)

    avg_height_growth = round(sum(height_deltas) / len(height_deltas), 2) if height_deltas else None
    avg_dbh_growth = round(sum(dbh_deltas) / len(dbh_deltas), 2) if dbh_deltas else None

    if survival_rate >= 85.0:
        tree_status = "Optimal"
        tree_score = 95.0
    elif survival_rate >= 70.0:
        tree_status = "Waspada"
        tree_score = 75.0
    else:
        tree_status = "Kritis"
        tree_score = 40.0

    tree_indicator = TreePerformanceIndicator(
        trees_planted=total_planted,
        trees_survived=total_survived,
        survival_rate_pct=survival_rate,
        status=tree_status,
        avg_height_growth_cm=avg_height_growth,
        avg_dbh_growth_cm=avg_dbh_growth,
    )

    # ── 3. Carbon Metrics & Density ──
    latest_carbon = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.project_id == project.id)
        .order_by(CarbonRecord.period_end.desc())
        .first()
    )

    carbon_stock = latest_carbon.carbon_stock_tco2e if latest_carbon else None
    est_co2e = latest_carbon.estimated_co2e if latest_carbon else None
    density = round(carbon_stock / project.area_ha, 2) if (carbon_stock and project.area_ha and project.area_ha > 0) else None

    carbon_score = 80.0 if carbon_stock else 60.0

    carbon_indicator = CarbonIndicator(
        carbon_stock_tco2e=carbon_stock,
        estimated_co2e=est_co2e,
        carbon_density_tco2e_per_ha=density,
        methodology=latest_carbon.methodology if latest_carbon else "IPCC Tier 1 / Estimation",
    )

    # ── 4. Biodiversity Richness Index ──
    all_bio = db.query(BiodiversityObservation).filter(BiodiversityObservation.project_id == project.id).all()
    unique_species = len(set(b.species_name for b in all_bio))
    fauna_count = sum(1 for b in all_bio if b.species_type == "fauna")
    flora_count = sum(1 for b in all_bio if b.species_type == "flora")

    if unique_species >= 10:
        bio_richness = "Tinggi"
        bio_score = 95.0
    elif unique_species >= 3:
        bio_richness = "Sedang"
        bio_score = 75.0
    else:
        bio_richness = "Rendah"
        bio_score = 50.0

    bio_indicator = BiodiversityIndicator(
        unique_species_count=unique_species,
        fauna_count=fauna_count,
        flora_count=flora_count,
        richness_index=bio_richness,
    )

    # ── 5. Community Reach ──
    community_records = db.query(CommunityData).filter(CommunityData.project_id == project.id).all()
    total_beneficiaries = sum(c.beneficiary_count for c in community_records)
    total_villages = len(set(c.village_name for c in community_records))
    total_investment = sum(c.community_investment for c in community_records)

    community_indicator = CommunityIndicator(
        total_beneficiaries=total_beneficiaries,
        total_villages=total_villages,
        total_investment_usd=total_investment,
    )

    # ── 6. Composite Health Score Calculation ──
    # Formula: 35% Vegetation + 35% Tree Survival + 15% Carbon + 15% Biodiversity
    # Minus penalty for active critical/high alerts
    raw_health = (veg_score * 0.35) + (tree_score * 0.35) + (carbon_score * 0.15) + (bio_score * 0.15)

    active_alerts = db.query(Alert).filter(Alert.project_id == project.id, Alert.is_resolved == False).all()
    alert_penalty = 0.0
    for al in active_alerts:
        if al.severity in ["critical", "high"]:
            alert_penalty += 8.0
        elif al.severity == "medium":
            alert_penalty += 3.0

    final_health_score = max(0.0, min(100.0, round(raw_health - alert_penalty, 1)))

    if final_health_score >= 85.0:
        health_cat = "Sangat Sehat"
    elif final_health_score >= 70.0:
        health_cat = "Sehat"
    elif final_health_score >= 50.0:
        health_cat = "Perlu Perhatian"
    else:
        health_cat = "Kritis"

    return ProjectIndicatorsResponse(
        project_id=project.id,
        project_name=project.name,
        project_type=project.project_type,
        evaluated_at=datetime.utcnow(),
        overall_health_score=final_health_score,
        health_category=health_cat,
        vegetation_health=veg_indicator,
        tree_performance=tree_indicator,
        carbon=carbon_indicator,
        biodiversity=bio_indicator,
        community=community_indicator,
    )

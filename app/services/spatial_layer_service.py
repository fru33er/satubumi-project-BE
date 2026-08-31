"""
services/spatial_layer_service.py — GIS Multi-Layer Spasial untuk SATUBUMI MONITOR

Mengemas seluruh data spasial proyek menjadi multi-layer GeoJSON siap render:
1. Boundary (Batas teritori proyek)
2. Monitoring Plots (Plot permanen, transek, sampling)
3. Project Activities (Titik/area kegiatan penanaman & restorasi)
4. Tree Locations (Lokasi penanaman pohon per-batch)
5. Active Alerts (Titik peringatan deforestasi / kebakaran aktif)
6. Field Reports (Titik laporan lapangan petugas GPS)
7. Biodiversity Observations (Titik temuan satwa & flora liar)
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.models.project import Project
from app.models.monitor import (
    MonitoringPlot, ProjectActivity, TreeRecord, Alert, FieldReport, BiodiversityObservation
)
from app.schemas.monitor import (
    GeoJSONFeature, GeoJSONFeatureCollection, MapLayerSummary, ProjectMapLayersResponse
)


def get_project_map_layers(db: Session, project: Project) -> ProjectMapLayersResponse:
    """
    Mengambil dan mengonversi seluruh data spasial proyek menjadi struktur multi-layer.
    """
    all_lngs = []
    all_lats = []

    # 1. Layer Boundary
    boundary_feature = None
    if project.boundary_geojson and isinstance(project.boundary_geojson, dict):
        boundary_feature = GeoJSONFeature(
            type="Feature",
            geometry=project.boundary_geojson,
            properties={
                "project_id": project.id,
                "name": project.name,
                "project_type": project.project_type,
                "area_ha": project.area_ha,
                "location_name": project.location_name,
                "status": project.status,
            }
        )
        _extract_coords_from_geojson(project.boundary_geojson, all_lngs, all_lats)

    # 2. Layer Monitoring Plots
    plot_records = db.query(MonitoringPlot).filter(MonitoringPlot.project_id == project.id).all()
    plot_features = []
    for p in plot_records:
        if p.location_geojson and isinstance(p.location_geojson, dict):
            feat = GeoJSONFeature(
                type="Feature",
                geometry=p.location_geojson,
                properties={
                    "id": p.id,
                    "plot_code": p.plot_code,
                    "plot_name": p.plot_name,
                    "plot_type": p.plot_type,
                    "area_ha": p.area_ha,
                    "status": p.status,
                    "notes": p.notes,
                }
            )
            plot_features.append(feat)
            _extract_coords_from_geojson(p.location_geojson, all_lngs, all_lats)

    # 3. Layer Activities
    activity_records = db.query(ProjectActivity).filter(ProjectActivity.project_id == project.id).all()
    activity_features = []
    for a in activity_records:
        if a.location_geojson and isinstance(a.location_geojson, dict):
            feat = GeoJSONFeature(
                type="Feature",
                geometry=a.location_geojson,
                properties={
                    "id": a.id,
                    "activity_type": a.activity_type,
                    "activity_date": a.activity_date.isoformat() if a.activity_date else None,
                    "target": a.target,
                    "realization": a.realization,
                    "unit": a.unit,
                    "executor": a.executor,
                    "has_photo": bool(a.photo_urls),
                }
            )
            activity_features.append(feat)
            _extract_coords_from_geojson(a.location_geojson, all_lngs, all_lats)

    # 4. Layer Tree Locations
    tree_records = db.query(TreeRecord).filter(TreeRecord.project_id == project.id).all()
    tree_features = []
    for t in tree_records:
        if t.location_geojson and isinstance(t.location_geojson, dict):
            feat = GeoJSONFeature(
                type="Feature",
                geometry=t.location_geojson,
                properties={
                    "id": t.id,
                    "plot_id": t.plot_id,
                    "species": t.species,
                    "quantity": t.quantity,
                    "planting_date": t.planting_date.isoformat() if t.planting_date else None,
                    "condition": t.condition,
                    "is_alive": t.is_alive,
                }
            )
            tree_features.append(feat)
            _extract_coords_from_geojson(t.location_geojson, all_lngs, all_lats)

    # 5. Layer Alerts (Active Alerts with coordinates)
    alert_records = db.query(Alert).filter(Alert.project_id == project.id, Alert.is_resolved == False).all()
    alert_features = []
    for al in alert_records:
        if al.location_geojson and isinstance(al.location_geojson, dict):
            feat = GeoJSONFeature(
                type="Feature",
                geometry=al.location_geojson,
                properties={
                    "id": al.id,
                    "alert_type": al.alert_type,
                    "severity": al.severity,
                    "description": al.description,
                    "is_read": al.is_read,
                    "created_at": al.created_at.isoformat() if al.created_at else None,
                }
            )
            alert_features.append(feat)
            _extract_coords_from_geojson(al.location_geojson, all_lngs, all_lats)

    # 6. Layer Field Reports
    field_reports = db.query(FieldReport).filter(FieldReport.project_id == project.id).all()
    report_features = []
    for fr in field_reports:
        if fr.location_geojson and isinstance(fr.location_geojson, dict):
            feat = GeoJSONFeature(
                type="Feature",
                geometry=fr.location_geojson,
                properties={
                    "id": fr.id,
                    "officer_name": fr.officer_name,
                    "report_type": fr.report_type,
                    "plot_id": fr.plot_id,
                    "report_date": fr.report_date.isoformat() if fr.report_date else None,
                    "has_photos": bool(fr.photo_urls),
                    "has_videos": bool(fr.video_urls),
                }
            )
            report_features.append(feat)
            _extract_coords_from_geojson(fr.location_geojson, all_lngs, all_lats)

    # 7. Layer Biodiversity
    biodiversity_records = db.query(BiodiversityObservation).filter(BiodiversityObservation.project_id == project.id).all()
    bio_features = []
    for b in biodiversity_records:
        if b.location_geojson and isinstance(b.location_geojson, dict):
            feat = GeoJSONFeature(
                type="Feature",
                geometry=b.location_geojson,
                properties={
                    "id": b.id,
                    "species_name": b.species_name,
                    "species_type": b.species_type,
                    "observed_date": b.observed_date.isoformat() if b.observed_date else None,
                    "habitat": b.habitat,
                    "observer": b.observer,
                    "photo_url": b.photo_url,
                }
            )
            bio_features.append(feat)
            _extract_coords_from_geojson(b.location_geojson, all_lngs, all_lats)

    # Calculate center coordinates [lng, lat]
    center_coords = None
    if all_lngs and all_lats:
        center_coords = [
            round(sum(all_lngs) / len(all_lngs), 6),
            round(sum(all_lats) / len(all_lats), 6),
        ]

    summary = MapLayerSummary(
        total_plots=len(plot_features),
        total_activities=len(activity_features),
        total_tree_batches=len(tree_features),
        total_alerts=len(alert_features),
        total_field_reports=len(report_features),
        total_biodiversity=len(bio_features),
        has_boundary=bool(boundary_feature),
        center_coordinates=center_coords,
    )

    return ProjectMapLayersResponse(
        project_id=project.id,
        project_name=project.name,
        boundary=boundary_feature,
        plots=GeoJSONFeatureCollection(total_features=len(plot_features), features=plot_features),
        activities=GeoJSONFeatureCollection(total_features=len(activity_features), features=activity_features),
        tree_locations=GeoJSONFeatureCollection(total_features=len(tree_features), features=tree_features),
        alerts=GeoJSONFeatureCollection(total_features=len(alert_features), features=alert_features),
        field_reports=GeoJSONFeatureCollection(total_features=len(report_features), features=report_features),
        biodiversity=GeoJSONFeatureCollection(total_features=len(bio_features), features=bio_features),
        summary=summary,
    )


def _extract_coords_from_geojson(geo: Dict[str, Any], lngs: List[float], lats: List[float]):
    """Helper untuk mengekstrak nilai koordinat guna kalkulasi titik tengah (center)."""
    coords = geo.get("coordinates")
    gtype = geo.get("type", "").lower()

    if not coords:
        return

    if gtype == "point" and len(coords) >= 2:
        lngs.append(coords[0])
        lats.append(coords[1])
    elif gtype == "polygon" and isinstance(coords, list) and coords:
        for ring in coords:
            for pt in ring:
                if len(pt) >= 2:
                    lngs.append(pt[0])
                    lats.append(pt[1])
    elif gtype == "multipolygon" and isinstance(coords, list):
        for poly in coords:
            for ring in poly:
                for pt in ring:
                    if len(pt) >= 2:
                        lngs.append(pt[0])
                        lats.append(pt[1])

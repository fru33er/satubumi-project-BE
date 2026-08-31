"""
services/evidence_service.py — Multimedia Timeline & Spatial Evidence Map

Menghubungkan dan mengagregasikan seluruh bukti/evidence lapangan dari berbagai sumber:
1. Field Reports (foto, video, koordinat GPS, petugas, tipe laporan)
2. Project Activities (foto kegiatan tanam/restorasi, realisasi, pelaksana)
3. Tree Records (foto penanaman bibit awal, jumlah, spesies, koordinat plot)
4. Tree Measurements (foto pengukuran berkala, data pertumbuhan tinggi & DBH)
5. Biodiversity Observations (foto temuan satwa/flora, observer, habitat)
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, date, time

from app.models.monitor import (
    FieldReport, ProjectActivity, TreeRecord, TreeMeasurement, BiodiversityObservation
)
from app.schemas.monitor import (
    EvidenceItem, EvidenceTimelineResponse, GeoJSONFeature, EvidenceMapResponse
)


def get_evidence_timeline(
    db: Session,
    project_id: int,
    page: int = 1,
    limit: int = 20,
    source_type: Optional[str] = None,
    media_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> EvidenceTimelineResponse:
    """
    Mengumpulkan seluruh bukti lapangan menjadi satu feed timeline kronologis.
    """
    all_items: List[EvidenceItem] = []

    # 1. Field Reports
    if not source_type or source_type == "field_report":
        reports = db.query(FieldReport).filter(FieldReport.project_id == project_id).all()
        for r in reports:
            photos = r.photo_urls if isinstance(r.photo_urls, list) else []
            videos = r.video_urls if isinstance(r.video_urls, list) else []
            all_items.append(EvidenceItem(
                id=f"field_report_{r.id}",
                source_type="field_report",
                source_id=r.id,
                timestamp=r.report_date,
                title=f"Laporan: {r.report_type.replace('_', ' ').title()}",
                description=r.result_description or r.activity_description,
                author=r.officer_name,
                plot_id=r.plot_id,
                photos=photos,
                videos=videos,
                location_geojson=r.location_geojson,
                metadata={
                    "report_type": r.report_type,
                    "activity_description": r.activity_description,
                    "tree_record_id": r.tree_record_id,
                    "biodiversity_id": r.biodiversity_id,
                }
            ))

    # 2. Project Activities
    if not source_type or source_type == "activity":
        activities = db.query(ProjectActivity).filter(ProjectActivity.project_id == project_id).all()
        for a in activities:
            photos = a.photo_urls if isinstance(a.photo_urls, list) else []
            ts = datetime.combine(a.activity_date, time.min)
            all_items.append(EvidenceItem(
                id=f"activity_{a.id}",
                source_type="activity",
                source_id=a.id,
                timestamp=ts,
                title=f"Kegiatan: {a.activity_type.replace('_', ' ').title()}",
                description=a.notes,
                author=a.executor,
                plot_id=None,
                photos=photos,
                videos=[],
                location_geojson=a.location_geojson,
                metadata={
                    "activity_type": a.activity_type,
                    "target": a.target,
                    "realization": a.realization,
                    "unit": a.unit,
                }
            ))

    # 3. Tree Records (Penanaman Bibit Awal)
    if not source_type or source_type == "tree_record":
        trees = db.query(TreeRecord).filter(TreeRecord.project_id == project_id).all()
        for t in trees:
            photos = t.photo_urls if isinstance(t.photo_urls, list) else []
            ts = datetime.combine(t.planting_date, time.min)
            all_items.append(EvidenceItem(
                id=f"tree_record_{t.id}",
                source_type="tree_record",
                source_id=t.id,
                timestamp=ts,
                title=f"Penanaman: {t.species} ({t.quantity} pohon)",
                description=t.notes,
                author=None,
                plot_id=t.plot_id,
                photos=photos,
                videos=[],
                location_geojson=t.location_geojson,
                metadata={
                    "species": t.species,
                    "quantity": t.quantity,
                    "condition": t.condition,
                    "height_cm": t.height_cm,
                    "dbh_cm": t.dbh_cm,
                    "is_alive": t.is_alive,
                }
            ))

    # 4. Tree Measurements (Pengukuran Berkala)
    if not source_type or source_type == "tree_measurement":
        measurements = db.query(TreeMeasurement).filter(TreeMeasurement.project_id == project_id).all()
        for m in measurements:
            photos = m.photo_urls if isinstance(m.photo_urls, list) else []
            ts = datetime.combine(m.measurement_date, time.min)
            all_items.append(EvidenceItem(
                id=f"tree_measurement_{m.id}",
                source_type="tree_measurement",
                source_id=m.id,
                timestamp=ts,
                title=f"Pengukuran Pohon Batch #{m.tree_record_id}",
                description=m.notes,
                author=m.measured_by,
                plot_id=None,
                photos=photos,
                videos=[],
                location_geojson=None,
                metadata={
                    "tree_record_id": m.tree_record_id,
                    "height_cm": m.height_cm,
                    "dbh_cm": m.dbh_cm,
                    "condition": m.condition,
                    "is_alive": m.is_alive,
                }
            ))

    # 5. Biodiversity Observations
    if not source_type or source_type == "biodiversity":
        observations = db.query(BiodiversityObservation).filter(BiodiversityObservation.project_id == project_id).all()
        for b in observations:
            photos = [b.photo_url] if b.photo_url else []
            ts = datetime.combine(b.observed_date, time.min)
            all_items.append(EvidenceItem(
                id=f"biodiversity_{b.id}",
                source_type="biodiversity",
                source_id=b.id,
                timestamp=ts,
                title=f"Observasi {b.species_type.title()}: {b.species_name}",
                description=b.notes,
                author=b.observer,
                plot_id=None,
                photos=photos,
                videos=[],
                location_geojson=b.location_geojson,
                metadata={
                    "species_name": b.species_name,
                    "species_type": b.species_type,
                    "habitat": b.habitat,
                }
            ))

    # ── Filter Berdasarkan Media & Tanggal ──
    filtered_items: List[EvidenceItem] = []
    for item in all_items:
        # Filter media type
        if media_type == "photo" and not item.photos:
            continue
        if media_type == "video" and not item.videos:
            continue
        if media_type == "has_media" and not (item.photos or item.videos):
            continue

        # Filter tanggal
        item_date = item.timestamp.date()
        if start_date and item_date < start_date:
            continue
        if end_date and item_date > end_date:
            continue

        filtered_items.append(item)

    # Urutkan berdasarkan timestamp terbaru (descending)
    filtered_items.sort(key=lambda x: x.timestamp, reverse=True)

    total_items = len(filtered_items)
    offset = (page - 1) * limit
    paged_items = filtered_items[offset : offset + limit]

    return EvidenceTimelineResponse(
        project_id=project_id,
        total_items=total_items,
        page=page,
        limit=limit,
        items=paged_items,
    )


def get_evidence_map(
    db: Session,
    project_id: int,
    source_type: Optional[str] = None,
    has_media_only: bool = False,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> EvidenceMapResponse:
    """
    Mengumpulkan seluruh data evidence spasial yang memiliki koordinat GPS / GeoJSON
    dan mengemasnya dalam format standar GeoJSON FeatureCollection.
    """
    timeline_data = get_evidence_timeline(
        db=db,
        project_id=project_id,
        page=1,
        limit=10000,  # Ambil semua titik untuk visualisasi peta
        source_type=source_type,
        media_type="has_media" if has_media_only else None,
        start_date=start_date,
        end_date=end_date,
    )

    features: List[GeoJSONFeature] = []

    for item in timeline_data.items:
        if not item.location_geojson:
            continue

        # Validasi GeoJSON format
        geo = item.location_geojson
        if not isinstance(geo, dict) or "type" not in geo or "coordinates" not in geo:
            continue

        thumbnail = item.photos[0] if item.photos else None
        has_media = bool(item.photos or item.videos)

        feature = GeoJSONFeature(
            type="Feature",
            geometry=geo,
            properties={
                "id": item.id,
                "source_type": item.source_type,
                "source_id": item.source_id,
                "title": item.title,
                "description": item.description,
                "date": item.timestamp.isoformat(),
                "author": item.author,
                "plot_id": item.plot_id,
                "photos": item.photos,
                "videos": item.videos,
                "thumbnail_url": thumbnail,
                "has_media": has_media,
                "metadata": item.metadata,
            }
        )
        features.append(feature)

    return EvidenceMapResponse(
        type="FeatureCollection",
        project_id=project_id,
        total_features=len(features),
        features=features,
    )

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.rapid_fs import RapidFSResult
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/assessments", tags=["Assessment History"])

@router.post("", status_code=status.HTTP_201_CREATED)
def save_assessment(
    result: RapidFSResult,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Menyimpan hasil kalkulasi Rapid-FS ke database histori proyek user.
    """
    new_assessment = Assessment(
        user_id=current_user.id if current_user else None,
        location_name=result.location_name,
        area_ha=result.area_ha,
        ecosystem_type=result.ecosystem_type,
        project_duration_years=result.project_duration_years,
        carbon_price_usd=result.carbon_price_usd,
        agb_ton=result.agb_ton,
        carbon_stock_tc=result.carbon_stock_tc,
        co2e_ton=result.co2e_ton,
        acc_total_credits=result.acc_total_credits,
        gross_revenue_usd=result.gross_revenue_usd,
        total_cost_usd=result.cost_breakdown.total_cost_usd,
        net_revenue_usd=result.net_revenue_usd,
        feasibility_score=result.feasibility_score,
        feasibility_category=result.feasibility_category,
        component_scores_json=result.component_scores.model_dump(),
        cost_breakdown_json=result.cost_breakdown.model_dump(),
        geometry_geojson=result.geometry,
        recommendations_json=result.recommendations
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    return {"id": new_assessment.id, "message": "Hasil assessment berhasil disimpan."}

@router.get("")
def list_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mendapatkan daftar histori assessment milik user terautentikasi.
    """
    if current_user.role == "admin":
        assessments = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
    else:
        assessments = db.query(Assessment).filter(Assessment.user_id == current_user.id).order_by(Assessment.created_at.desc()).all()
    return assessments

@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment tidak ditemukan.")
    if current_user.role != "admin" and assessment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Akses ditolak.")
    return assessment

@router.delete("/{assessment_id}")
def delete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment tidak ditemukan.")
    if current_user.role != "admin" and assessment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Akses ditolak.")
        
    db.delete(assessment)
    db.commit()
    return {"message": "Assessment berhasil dihapus."}

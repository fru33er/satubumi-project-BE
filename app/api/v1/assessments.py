from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.assessment import AssessmentSubmitRequest, AssessmentResponse
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/assessments", tags=["Assessment History"])


@router.post("", status_code=status.HTTP_201_CREATED)
def save_assessment(
    body: AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Menyimpan hasil kalkulasi Rapid-FS ke database histori assessment.

    - **submitter_name**: Nama lengkap user (opsional jika sudah login)
    - **submitter_phone**: Nomor telepon user
    - **submitter_email**: Email user
    - **rapid_fs_result**: Hasil lengkap dari endpoint `/rapid-fs/calculate`

    Jika user sudah login, `user_id` otomatis diisi. Data kontak tetap bisa dioverride manual.
    """
    result = body.rapid_fs_result

    # Jika user login & tidak mengisi submitter_name/email, fallback ke profil user
    submitter_name = body.submitter_name
    submitter_email = body.submitter_email
    if current_user:
        if not submitter_name and current_user.full_name:
            submitter_name = current_user.full_name
        if not submitter_email and current_user.email:
            submitter_email = current_user.email

    new_assessment = Assessment(
        user_id=current_user.id if current_user else None,
        submitter_name=submitter_name,
        submitter_phone=body.submitter_phone,
        submitter_email=submitter_email,
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
    return {
        "id": new_assessment.id,
        "message": "Hasil assessment berhasil disimpan.",
        "submitter_name": new_assessment.submitter_name,
        "submitter_email": new_assessment.submitter_email
    }


@router.get("", response_model=List[AssessmentResponse])
def list_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mendapatkan daftar histori assessment.

    - **Admin**: Melihat semua assessment dari semua user beserta data kontak submitter.
    - **User biasa**: Hanya melihat assessment miliknya sendiri.
    """
    if current_user.role == "admin":
        assessments = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
    else:
        assessments = (
            db.query(Assessment)
            .filter(Assessment.user_id == current_user.id)
            .order_by(Assessment.created_at.desc())
            .all()
        )
    return assessments


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mendapatkan detail satu assessment berdasarkan ID.
    Admin bisa akses semua; user biasa hanya miliknya.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment tidak ditemukan.")
    if current_user.role != "admin" and assessment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Akses ditolak.")
    return assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_200_OK)
def delete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menghapus assessment berdasarkan ID.
    Admin bisa hapus semua; user biasa hanya miliknya.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment tidak ditemukan.")
    if current_user.role != "admin" and assessment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Akses ditolak.")

    db.delete(assessment)
    db.commit()
    return {"message": "Assessment berhasil dihapus."}

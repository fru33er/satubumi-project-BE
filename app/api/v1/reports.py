from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.assessment import Assessment
from app.services.pdf_generator import generate_pdf_report

router = APIRouter(prefix="/reports", tags=["PDF Reports"])

@router.get("/{assessment_id}/pdf")
def download_pdf(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment tidak ditemukan.")
        
    assessment_data = {
        "location_name": assessment.location_name,
        "area_ha": assessment.area_ha,
        "ecosystem_type": assessment.ecosystem_type,
        "project_duration_years": assessment.project_duration_years,
        "carbon_price_usd": assessment.carbon_price_usd,
        "feasibility_score": assessment.feasibility_score,
        "feasibility_category": assessment.feasibility_category,
        "agb_ton": assessment.agb_ton,
        "carbon_stock_tc": assessment.carbon_stock_tc,
        "co2e_ton": assessment.co2e_ton,
        "annual_emission_reduction": assessment.acc_total_credits / max(1, assessment.project_duration_years),
        "acc_total_credits": assessment.acc_total_credits,
        "gross_revenue_usd": assessment.gross_revenue_usd,
        "total_cost_usd": assessment.total_cost_usd,
        "net_revenue_usd": assessment.net_revenue_usd,
        "recommendations": assessment.recommendations_json or []
    }
    
    pdf_content = generate_pdf_report(assessment_data)
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Satubumi_RapidFS_{assessment_id}.pdf"}
    )

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter(prefix="/contact", tags=["Contact & Inquiries"])

class ContactInquiry(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    service_interest: Optional[str] = "General Inquiry"
    message: str

@router.post("", status_code=status.HTTP_201_CREATED)
def submit_contact(inquiry: ContactInquiry):
    """
    Menerima formulir pesan kontak/inquiry dari calon klien Satubumi.org.
    """
    return {
        "status": "success",
        "message": f"Terima kasih {inquiry.name}, pesan Anda telah berhasil dikirim ke tim Satubumi."
    }

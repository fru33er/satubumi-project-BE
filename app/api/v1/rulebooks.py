import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.rulebook import Rulebook
from app.models.rulebook_download import RulebookDownload
from app.models.user import User
from app.schemas.rulebook import (
    RulebookDownloadCreate,
    RulebookResponse,
)

router = APIRouter(
    prefix="/rulebooks",
    tags=["Rulebooks"],
)


RULEBOOK_UPLOAD_DIR = "static/rulebooks"

ALLOWED_PDF_TYPES = {
    "application/pdf",
}

MAX_PDF_SIZE = 25 * 1024 * 1024


os.makedirs(
    RULEBOOK_UPLOAD_DIR,
    exist_ok=True,
)


def serialize_rulebook(rulebook: Rulebook):
    return {
        "id": rulebook.id,
        "title": rulebook.title,
        "description": rulebook.description,
        "file_url": rulebook.file_url,
        "thumbnail_url": rulebook.thumbnail_url,
        "status": rulebook.status,
        "download_count": rulebook.download_count or 0,
        "created_at": rulebook.created_at,
        "updated_at": rulebook.updated_at,
    }


def delete_rulebook_file(file_url: str | None):
    if not file_url:
        return

    try:
        filename = file_url.split("/")[-1]

        file_path = os.path.join(
            RULEBOOK_UPLOAD_DIR,
            filename,
        )

        if os.path.isfile(file_path):
            os.remove(file_path)

    except Exception:
        pass


# =========================================================
# PUBLIC
# =========================================================


@router.get(
    "/",
    response_model=list[RulebookResponse],
)
def list_rulebooks(
    db: Session = Depends(get_db),
):
    rulebooks = (
        db.query(Rulebook)
        .filter(Rulebook.status == "published")
        .order_by(Rulebook.created_at.desc())
        .all()
    )

    return [serialize_rulebook(item) for item in rulebooks]


@router.post(
    "/{rulebook_id}/download",
)
def download_rulebook(
    rulebook_id: int,
    data: RulebookDownloadCreate,
    db: Session = Depends(get_db),
):
    rulebook = db.query(Rulebook).filter(Rulebook.id == rulebook_id).first()

    if not rulebook:
        raise HTTPException(
            status_code=404,
            detail="Rulebook tidak ditemukan.",
        )

    if rulebook.status != "published":
        raise HTTPException(
            status_code=404,
            detail="Rulebook tidak tersedia.",
        )

    download = RulebookDownload(
        rulebook_id=rulebook.id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        institution=data.institution,
    )

    db.add(download)

    rulebook.download_count = (rulebook.download_count or 0) + 1

    db.commit()

    return {
        "message": "Download recorded",
        "download_url": rulebook.file_url,
    }


# =========================================================
# ADMIN
# =========================================================


@router.get(
    "/admin/all",
    response_model=list[RulebookResponse],
)
def admin_list_rulebooks(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rulebooks = db.query(Rulebook).order_by(Rulebook.created_at.desc()).all()

    return [serialize_rulebook(item) for item in rulebooks]


@router.post(
    "/admin/upload",
    response_model=RulebookResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_rulebook(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    status_value: str = Form(
        "published",
        alias="status",
    ),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if status_value not in {
        "published",
        "draft",
    }:
        raise HTTPException(
            status_code=400,
            detail="Status harus published atau draft.",
        )

    if file.content_type not in ALLOWED_PDF_TYPES:
        raise HTTPException(
            status_code=400,
            detail="File harus berformat PDF.",
        )

    extension = os.path.splitext(file.filename or "")[1].lower()

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="File harus memiliki ekstensi .pdf.",
        )

    contents = await file.read()

    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Ukuran PDF maksimal 25MB.",
        )

    unique_filename = f"{uuid.uuid4().hex}.pdf"

    file_path = os.path.join(
        RULEBOOK_UPLOAD_DIR,
        unique_filename,
    )

    with open(
        file_path,
        "wb",
    ) as buffer:
        buffer.write(contents)

    base_url = str(request.base_url).rstrip("/")

    file_url = f"{base_url}/static/rulebooks/{unique_filename}"

    rulebook = Rulebook(
        title=title.strip(),
        description=(description.strip() if description else None),
        file_url=file_url,
        status=status_value,
        download_count=0,
    )

    db.add(rulebook)

    db.commit()

    db.refresh(rulebook)

    return serialize_rulebook(rulebook)


@router.put(
    "/admin/{rulebook_id}",
    response_model=RulebookResponse,
)
def update_rulebook(
    rulebook_id: int,
    title: str = Form(...),
    description: str = Form(""),
    status_value: str = Form(
        "published",
        alias="status",
    ),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rulebook = db.query(Rulebook).filter(Rulebook.id == rulebook_id).first()

    if not rulebook:
        raise HTTPException(
            status_code=404,
            detail="Rulebook tidak ditemukan.",
        )

    if status_value not in {
        "published",
        "draft",
    }:
        raise HTTPException(
            status_code=400,
            detail="Status harus published atau draft.",
        )

    rulebook.title = title.strip()

    rulebook.description = description.strip() if description else None

    rulebook.status = status_value

    db.commit()

    db.refresh(rulebook)

    return serialize_rulebook(rulebook)


@router.delete(
    "/admin/{rulebook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_rulebook(
    rulebook_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rulebook = db.query(Rulebook).filter(Rulebook.id == rulebook_id).first()

    if not rulebook:
        raise HTTPException(
            status_code=404,
            detail="Rulebook tidak ditemukan.",
        )

    delete_rulebook_file(rulebook.file_url)

    db.query(RulebookDownload).filter(
        RulebookDownload.rulebook_id == rulebook.id
    ).delete(synchronize_session=False)

    db.delete(rulebook)

    db.commit()


@router.get(
    "/admin/{rulebook_id}/downloads",
)
def rulebook_downloads(
    rulebook_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rulebook = db.query(Rulebook).filter(Rulebook.id == rulebook_id).first()

    if not rulebook:
        raise HTTPException(
            status_code=404,
            detail="Rulebook tidak ditemukan.",
        )

    downloads = (
        db.query(RulebookDownload)
        .filter(RulebookDownload.rulebook_id == rulebook_id)
        .order_by(RulebookDownload.created_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "name": item.name,
            "email": item.email,
            "phone": item.phone,
            "institution": item.institution,
            "created_at": item.created_at,
        }
        for item in downloads
    ]

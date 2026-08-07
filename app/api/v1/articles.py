import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.config import settings
from app.models.user import User
from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse

router = APIRouter(prefix="/articles", tags=["Articles & Content (About & Services)"])

# Format gambar yang diizinkan
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@router.get("/", response_model=List[ArticleResponse])
def get_articles(category: Optional[str] = Query(None, description="Filter: 'about' or 'services'"), db: Session = Depends(get_db)):
    """Ambil semua artikel (Publik). Bisa difilter ?category=about atau ?category=services"""
    query = db.query(Article)
    if category:
        query = query.filter(Article.category == category)
    return query.order_by(Article.created_at.desc()).all()

@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """Ambil detail artikel berdasarkan ID"""
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")
    return art

@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    article_in: ArticleCreate, 
    db: Session = Depends(get_db), 
    admin: User = Depends(require_admin)
):
    """[Admin & Super Admin] Buat artikel baru untuk About atau Services"""
    new_art = Article(**article_in.dict())
    db.add(new_art)
    db.commit()
    db.refresh(new_art)
    return new_art

@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: int, 
    article_in: ArticleUpdate, 
    db: Session = Depends(get_db), 
    admin: User = Depends(require_admin)
):
    """[Admin & Super Admin] Update artikel"""
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")
    
    for key, value in article_in.dict(exclude_unset=True).items():
        setattr(art, key, value)
    
    db.commit()
    db.refresh(art)
    return art

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int, 
    db: Session = Depends(get_db), 
    admin: User = Depends(require_admin)
):
    """[Admin & Super Admin] Hapus artikel"""
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")
    
    # Hapus file gambar dari disk jika ada
    if art.image_url:
        _delete_image_file(art.image_url)
    
    db.delete(art)
    db.commit()


# ──────────────────────────────────────────────
# Endpoint Upload & Hapus Gambar Artikel
# ──────────────────────────────────────────────

@router.post(
    "/{article_id}/image",
    response_model=ArticleResponse,
    summary="Upload Gambar Artikel",
)
async def upload_article_image(
    article_id: int,
    request: Request,
    file: UploadFile = File(..., description="File gambar (jpg, jpeg, png, webp). Maks 5 MB."),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    [Admin & Super Admin] Upload atau ganti gambar untuk artikel tertentu.

    - **Format yang didukung**: `jpg`, `jpeg`, `png`, `webp`
    - **Ukuran maksimal**: 5 MB
    - Gambar lama otomatis **dihapus** dari server saat diganti.
    - URL gambar tersimpan di field `image_url` pada response.
    - Gambar bisa diakses publik via: `GET /static/uploads/{filename}`
    """
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")

    # --- Validasi tipe file ---
    content_type = file.content_type or ""
    ext = os.path.splitext(file.filename or "")[1].lower()

    if content_type not in ALLOWED_IMAGE_TYPES or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format file tidak didukung. Gunakan: jpg, jpeg, png, atau webp."
        )

    # --- Baca konten & validasi ukuran ---
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Ukuran file melebihi batas maksimal {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    # --- Hapus gambar lama dari disk jika ada ---
    if art.image_url:
        _delete_image_file(art.image_url)

    # --- Simpan file baru dengan nama unik ---
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    upload_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(upload_path, "wb") as f:
        f.write(contents)

    # --- Bangun URL publik gambar ---
    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}/static/uploads/{unique_filename}"

    # --- Update DB ---
    art.image_url = public_url
    db.commit()
    db.refresh(art)

    return art


@router.delete(
    "/{article_id}/image",
    response_model=ArticleResponse,
    summary="Hapus Gambar Artikel",
)
def delete_article_image(
    article_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    [Admin & Super Admin] Hapus gambar dari artikel.

    - File gambar dihapus dari server.
    - Field `image_url` di artikel di-set menjadi `null`.
    """
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")

    if not art.image_url:
        raise HTTPException(status_code=404, detail="Artikel ini tidak memiliki gambar.")

    # Hapus file dari disk
    _delete_image_file(art.image_url)

    # Reset image_url di DB
    art.image_url = None
    db.commit()
    db.refresh(art)

    return art


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def _delete_image_file(image_url: str) -> None:
    """Hapus file gambar dari disk berdasarkan URL-nya. Tidak raise error jika file tidak ada."""
    try:
        # Ambil nama file dari URL (bagian terakhir setelah '/uploads/')
        filename = image_url.split("/uploads/")[-1]
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception:
        pass  # Jika gagal hapus file, abaikan (tidak blokir operasi DB)

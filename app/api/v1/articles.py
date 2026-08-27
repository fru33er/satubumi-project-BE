import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.article import Article
from app.models.user import User
from app.schemas.article import (
    ArticleCreate,
    ArticleResponse,
    ArticleUpdate,
    TopAuthorItem,
    TopicItem,
)

router = APIRouter(prefix="/articles", tags=["Articles & Content"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def serialize_article(art: Article, lang: str = "id") -> dict:
    """
    lang=id → title/content Indonesia
    lang=en → title_en/content_en (fallback ke ID jika kosong)
    """
    use_en = lang == "en"
    return {
        "id": art.id,
        "category": art.category,
        "title": (art.title_en if use_en and art.title_en else art.title),
        "title_en": getattr(art, "title_en", None),
        "slug": art.slug,
        "author": art.author or "Satubumi Team",
        "author_profile_image": (
            art.author_user.profile_image if art.author_user else None
        ),
        "content": (art.content_en if use_en and art.content_en else art.content),
        "content_en": getattr(art, "content_en", None),
        "status": art.status,
        "tags": art.tags,
        "image_url": art.image_url,
        "topic": getattr(art, "topic", None),
        "is_featured": bool(getattr(art, "is_featured", False)),
        "view_count": int(getattr(art, "view_count", 0) or 0),
        "created_at": art.created_at,
        "updated_at": art.updated_at,
    }


def _delete_image_file(image_url: str) -> None:
    try:
        filename = image_url.split("/uploads/")[-1]
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception:
        pass


# ──────────────────────────────────────────────
# LIST & FILTER (publik)
# ──────────────────────────────────────────────


@router.get("/", response_model=list[ArticleResponse])
async def get_articles(
    category: str | None = Query(
        None, description="about | services | insight | home | ..."
    ),
    topic: str | None = Query(
        None, description="carbon | esg | policy | nature | other"
    ),
    is_featured: bool | None = Query(None),
    author: str | None = Query(None),
    lang: str = Query("id", description="id | en"),
    db: Session = Depends(get_db),
):
    query = db.query(Article)
    if category:
        query = query.filter(Article.category == category)
    if topic:
        query = query.filter(Article.topic == topic)
    if is_featured is not None:
        query = query.filter(Article.is_featured == is_featured)
    if author:
        query = query.filter(Article.author == author)

    articles = query.order_by(Article.created_at.desc()).all()
    return [serialize_article(art, lang) for art in articles]


# ──────────────────────────────────────────────
# INSIGHTS STATS (HARUS di atas /{article_id})
# ──────────────────────────────────────────────


@router.get("/insights/top", response_model=list[ArticleResponse])
def get_top_insights(
    limit: int = Query(5, ge=1, le=20),
    by: str = Query("featured", description="featured | views | recent"),
    lang: str = Query("id"),
    db: Session = Depends(get_db),
):
    q = db.query(Article).filter(
        Article.category == "insight",
        Article.status == "published",
    )
    if by == "featured":
        q = q.filter(Article.is_featured == True).order_by(Article.updated_at.desc())
    elif by == "views":
        q = q.order_by(desc(Article.view_count), Article.created_at.desc())
    else:
        q = q.order_by(Article.created_at.desc())

    articles = q.limit(limit).all()
    return [serialize_article(art, lang) for art in articles]


@router.get("/insights/top-authors", response_model=list[TopAuthorItem])
def get_top_authors(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Article.author, func.count(Article.id).label("count"))
        .filter(
            Article.category == "insight",
            Article.status == "published",
        )
        .group_by(Article.author)
        .order_by(desc("count"))
        .limit(limit)
        .all()
    )
    return [
        TopAuthorItem(author=(r.author or "Satubumi Team"), count=r.count) for r in rows
    ]


@router.get("/insights/topics", response_model=list[TopicItem])
def get_insight_topics(db: Session = Depends(get_db)):
    rows = (
        db.query(Article.topic, func.count(Article.id).label("count"))
        .filter(
            Article.category == "insight",
            Article.status == "published",
            Article.topic.isnot(None),
            Article.topic != "",
        )
        .group_by(Article.topic)
        .order_by(desc("count"))
        .all()
    )
    return [TopicItem(topic=r.topic, count=r.count) for r in rows]


@router.post("/{article_id}/view", response_model=ArticleResponse)
def increment_article_view(
    article_id: int,
    lang: str = Query("id"),
    db: Session = Depends(get_db),
):
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")
    if art.category == "insight" and art.status == "published":
        art.view_count = int(getattr(art, "view_count", 0) or 0) + 1
        db.commit()
        db.refresh(art)
    return serialize_article(art, lang)


# ──────────────────────────────────────────────
# DETAIL BY ID
# ──────────────────────────────────────────────


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    lang: str = Query("id", description="id | en"),
    db: Session = Depends(get_db),
):
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")
    return serialize_article(art, lang)


# ──────────────────────────────────────────────
# CRUD (admin)
# ──────────────────────────────────────────────


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    article_in: ArticleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = article_in.dict()
    if getattr(admin, "full_name", None):
        data["author"] = admin.full_name
        data["author_id"] = admin.id
    data.setdefault("is_featured", False)
    data.setdefault("view_count", 0)

    allowed = {c.name for c in Article.__table__.columns}
    payload = {k: v for k, v in data.items() if k in allowed}

    new_art = Article(**payload)
    db.add(new_art)
    db.commit()
    db.refresh(new_art)
    return serialize_article(new_art, "id")


@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: int,
    article_in: ArticleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")

    allowed = {c.name for c in Article.__table__.columns}
    for key, value in article_in.dict(exclude_unset=True).items():
        if key in allowed:
            setattr(art, key, value)

    db.commit()
    db.refresh(art)
    return serialize_article(art, "id")


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")

    if art.image_url:
        _delete_image_file(art.image_url)

    db.delete(art)
    db.commit()


# ──────────────────────────────────────────────
# IMAGE
# ──────────────────────────────────────────────


@router.post(
    "/{article_id}/image",
    response_model=ArticleResponse,
    summary="Upload Gambar Artikel",
)
async def upload_article_image(
    article_id: int,
    request: Request,
    file: UploadFile = File(..., description="jpg, jpeg, png, webp. Maks 5 MB."),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")

    content_type = file.content_type or ""
    ext = os.path.splitext(file.filename or "")[1].lower()

    if content_type not in ALLOWED_IMAGE_TYPES or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Format file tidak didukung. Gunakan: jpg, jpeg, png, atau webp.",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Ukuran file melebihi batas maksimal {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    if art.image_url:
        _delete_image_file(art.image_url)

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    upload_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    with open(upload_path, "wb") as f:
        f.write(contents)

    base_url = str(request.base_url).rstrip("/")
    art.image_url = f"{base_url}/static/uploads/{unique_filename}"
    db.commit()
    db.refresh(art)
    return serialize_article(art, "id")


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
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")
    if not art.image_url:
        raise HTTPException(
            status_code=404, detail="Artikel ini tidak memiliki gambar."
        )

    _delete_image_file(art.image_url)
    art.image_url = None
    db.commit()
    db.refresh(art)
    return serialize_article(art, "id")

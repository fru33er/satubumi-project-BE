from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.insight_topic import InsightTopic
from app.models.article import Article
from app.schemas.insight_topic import (
    InsightTopicCreate,
    InsightTopicUpdate,
    InsightTopicResponse,
    slugify,
)

router = APIRouter(prefix="/insight-topics", tags=["Insight Topics"])


@router.get("/", response_model=List[InsightTopicResponse])
def list_topics(db: Session = Depends(get_db)):
    """Publik + admin: daftar semua topic (untuk dropdown & filter)."""
    return db.query(InsightTopic).order_by(InsightTopic.label_en.asc()).all()


@router.post("/", response_model=InsightTopicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(
    body: InsightTopicCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    slug = slugify(body.slug or body.label_en or body.label_id)
    exists = db.query(InsightTopic).filter(InsightTopic.slug == slug).first()
    if exists:
        raise HTTPException(status_code=400, detail="Slug topic sudah dipakai.")

    row = InsightTopic(
        slug=slug,
        label_id=body.label_id.strip(),
        label_en=body.label_en.strip(),
        created_by=getattr(admin, "full_name", None) or admin.email,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{topic_id}", response_model=InsightTopicResponse)
def update_topic(
    topic_id: int,
    body: InsightTopicUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    row = db.query(InsightTopic).filter(InsightTopic.id == topic_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Topic tidak ditemukan.")

    data = body.dict(exclude_unset=True)
    if "slug" in data and data["slug"]:
        new_slug = slugify(data["slug"])
        clash = (
            db.query(InsightTopic)
            .filter(InsightTopic.slug == new_slug, InsightTopic.id != topic_id)
            .first()
        )
        if clash:
            raise HTTPException(status_code=400, detail="Slug sudah dipakai.")
        old_slug = row.slug
        row.slug = new_slug
        # sync artikel yang masih pakai slug lama
        db.query(Article).filter(
            Article.category == "insight", Article.topic == old_slug
        ).update({Article.topic: new_slug}, synchronize_session=False)
    if "label_id" in data and data["label_id"]:
        row.label_id = data["label_id"].strip()
    if "label_en" in data and data["label_en"]:
        row.label_en = data["label_en"].strip()

    db.commit()
    db.refresh(row)
    return row


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    row = db.query(InsightTopic).filter(InsightTopic.id == topic_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Topic tidak ditemukan.")

    used = (
        db.query(Article)
        .filter(Article.category == "insight", Article.topic == row.slug)
        .count()
    )
    if used > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Topic masih dipakai {used} insight. Pindahkan dulu sebelum hapus.",
        )

    db.delete(row)
    db.commit()
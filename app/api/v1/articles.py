from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse

router = APIRouter(prefix="/articles", tags=["Articles & Content (About & Services)"])

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
    db.delete(art)
    db.commit()

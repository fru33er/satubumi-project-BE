from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArticleBase(BaseModel):
    category: str  # about | services | home | insight | general
    title: str
    title_en: Optional[str] = None
    slug: Optional[str] = None
    author: Optional[str] = "Satubumi Team"
    content: str
    content_en: Optional[str] = None
    status: Optional[str] = "published"
    tags: Optional[str] = None
    image_url: Optional[str] = None
    # Insights
    topic: Optional[str] = None  # carbon | esg | policy | nature | other
    is_featured: Optional[bool] = False


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    title_en: Optional[str] = None
    slug: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    content_en: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[str] = None
    image_url: Optional[str] = None
    topic: Optional[str] = None
    is_featured: Optional[bool] = None


class ArticleResponse(ArticleBase):
    id: int
    view_count: int = 0
    is_featured: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopAuthorItem(BaseModel):
    author: str
    count: int


class TopicItem(BaseModel):
    topic: str
    count: int
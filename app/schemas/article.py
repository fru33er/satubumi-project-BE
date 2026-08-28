from datetime import datetime

from pydantic import BaseModel


class ArticleBase(BaseModel):
    category: str  # about | services | home | insight | general
    title: str
    title_en: str | None = None
    slug: str | None = None
    author: str | None = "Satubumi Team"
    content: str
    content_en: str | None = None
    status: str | None = "published"
    tags: str | None = None
    image_url: str | None = None
    # Insights
    topic: str | None = None  # carbon | esg | policy | nature | other
    is_featured: bool | None = False


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    category: str | None = None
    title: str | None = None
    title_en: str | None = None
    slug: str | None = None
    author: str | None = None
    content: str | None = None
    content_en: str | None = None
    status: str | None = None
    tags: str | None = None
    image_url: str | None = None
    topic: str | None = None
    is_featured: bool | None = None


class ArticleResponse(ArticleBase):
    id: int
    author_id: int | None = None
    author_profile_image: str | None = None
    view_count: int = 0
    is_featured: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopAuthorItem(BaseModel):
    author: str
    count: int
    author_profile_image: str | None = None


class TopicItem(BaseModel):
    topic: str
    count: int

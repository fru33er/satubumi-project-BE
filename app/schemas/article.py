from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArticleBase(BaseModel):
    category: str  # 'about' or 'services'
    title: str
    slug: Optional[str] = None
    author: Optional[str] = "Satubumi Team"
    content: str
    status: Optional[str] = "published"
    tags: Optional[str] = None

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    slug: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[str] = None

class ArticleResponse(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

import re
from datetime import datetime

from pydantic import BaseModel, Field


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:50] or "topic"


class InsightTopicBase(BaseModel):
    label_id: str = Field(..., min_length=1, max_length=100)
    label_en: str = Field(..., min_length=1, max_length=100)
    slug: str | None = None


class InsightTopicCreate(InsightTopicBase):
    pass


class InsightTopicUpdate(BaseModel):
    label_id: str | None = None
    label_en: str | None = None
    slug: str | None = None


class InsightTopicResponse(BaseModel):
    id: int
    slug: str
    label_id: str
    label_en: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

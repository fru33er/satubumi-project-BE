from datetime import datetime

from pydantic import BaseModel


class RulebookBase(BaseModel):
    title: str

    description: str | None = None


class RulebookResponse(RulebookBase):
    id: int

    file_url: str

    thumbnail_url: str | None = None

    download_count: int = 0

    created_at: datetime

    class Config:
        from_attributes = True


class RulebookDownloadCreate(BaseModel):
    name: str

    email: str

    phone: str

    institution: str

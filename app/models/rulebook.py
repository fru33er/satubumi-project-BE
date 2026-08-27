from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Rulebook(Base):
    __tablename__ = "rulebooks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)

    description = Column(Text, nullable=True)

    file_url = Column(String(500), nullable=False)

    thumbnail_url = Column(String(500), nullable=True)

    status = Column(String(30), default="published")

    download_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

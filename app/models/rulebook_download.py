from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


class RulebookDownload(Base):
    __tablename__ = "rulebook_downloads"

    id = Column(Integer, primary_key=True, index=True)

    rulebook_id = Column(Integer, ForeignKey("rulebooks.id"))

    name = Column(String(255), nullable=False)

    email = Column(String(255), nullable=False)

    phone = Column(String(50), nullable=False)

    institution = Column(String(255), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

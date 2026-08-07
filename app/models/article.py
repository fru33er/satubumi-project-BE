from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.core.database import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # 'about', 'services', 'general'
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True)
    author = Column(String(255), default="Satubumi Team")
    content = Column(Text, nullable=False)
    status = Column(String(30), default="published")  # 'published', 'draft'
    tags = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)  # URL path gambar artikel (opsional)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

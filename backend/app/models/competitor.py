from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    followers_count = Column(Integer, default=0)
    category = Column(String(100), default="Tech", nullable=True)
    country = Column(String(100), default="India", nullable=True)
    custom_view_threshold = Column(Integer, default=500000)
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=True, index=True)
    creator = relationship("Creator", foreign_keys=[creator_id])

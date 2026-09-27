from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Creator(Base):
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, index=True)
    platform_user_id = Column(String(100), unique=True, nullable=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(Text, nullable=True)
    profile_pic_url = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    biography = Column(Text, nullable=True)
    profile_url = Column(Text, nullable=True)
    country = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    reels = relationship("Reel", back_populates="creator")

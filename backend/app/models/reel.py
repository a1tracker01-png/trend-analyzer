from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Reel(Base):
    __tablename__ = "reels"

    id = Column(Integer, primary_key=True, index=True)
    platform_media_id = Column(String(150), unique=True, nullable=False, index=True)
    permalink = Column(String(500), nullable=False)
    caption = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    duration = Column(Float, default=0.0)
    posted_at = Column(DateTime(timezone=True), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Latest cached metrics for fast, SQL-standard compliant queries & indexing
    current_views = Column(Integer, default=0, index=True)
    current_likes = Column(Integer, default=0, index=True)
    current_comments = Column(Integer, default=0, index=True)
    current_shares = Column(Integer, default=0, index=True)
    current_saves = Column(Integer, default=0)
    current_engagement_rate = Column(Float, default=0.0, index=True)
    current_trending_score = Column(Float, default=0.0, index=True)
    current_growth_velocity = Column(Float, default=0.0, index=True)
    current_rank = Column(Integer, nullable=True, index=True)

    category = relationship("Category", back_populates="reels")
    creator = relationship("Creator", back_populates="reels")
    data_source = relationship("DataSource", back_populates="reels")
    metrics = relationship("ReelMetrics", back_populates="reel", cascade="all, delete-orphan", order_by="desc(ReelMetrics.recorded_at)")
    trending_scores = relationship("TrendingScore", back_populates="reel", cascade="all, delete-orphan", order_by="desc(TrendingScore.recorded_at)")

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base

class ReelMetrics(Base):
    __tablename__ = "reel_metrics"

    id = Column(Integer, primary_key=True, index=True)
    reel_id = Column(Integer, ForeignKey("reels.id"), nullable=False, index=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    save_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)  # Calculated: (likes + comments + shares) / views * 100
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    reel = relationship("Reel", back_populates="metrics")

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from backend.app.database import Base

class TrendingScore(Base):
    __tablename__ = "trending_scores"

    id = Column(Integer, primary_key=True, index=True)
    reel_id = Column(Integer, ForeignKey("reels.id"), nullable=False, index=True)
    period = Column(String(20), default="24h")
    score = Column(Float, default=0.0)               # Composite popularity score
    growth_velocity = Column(Float, default=0.0)     # Views or engagements gained per hour
    rank = Column(Integer, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    reel = relationship("Reel", back_populates="trending_scores")

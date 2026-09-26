from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(String(50), nullable=False)  # "official_graph_api", "mock_provider", "webhook"
    api_endpoint = Column(String(500), nullable=True)
    auth_type = Column(String(50), default="bearer")     # "oauth2_bearer", "api_key", "none"
    is_active = Column(Boolean, default=True)
    rate_limit_limit = Column(Integer, default=200)
    rate_limit_remaining = Column(Integer, default=200)
    rate_limit_reset_at = Column(DateTime(timezone=True), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    config_json = Column(Text, nullable=True)
    status_message = Column(String(200), default="Operational")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    reels = relationship("Reel", back_populates="data_source")

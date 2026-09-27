from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from backend.app.schemas.creator import CreatorResponse

class ReelMetricsResponse(BaseModel):
    id: int
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    save_count: int = 0
    engagement_rate: float = 0.0
    recorded_at: datetime

    class Config:
        from_attributes = True

class TrendingScoreResponse(BaseModel):
    id: int
    period: str
    score: float = 0.0
    growth_velocity: float = 0.0
    rank: Optional[int] = None
    recorded_at: datetime

    class Config:
        from_attributes = True

class ReelResponse(BaseModel):
    id: int
    platform_media_id: str
    permalink: str
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    duration: float = 0.0
    posted_at: datetime
    category_id: int
    category_name: Optional[str] = None
    country: Optional[str] = None
    creator: Optional[CreatorResponse] = None
    latest_metrics: Optional[ReelMetricsResponse] = None
    latest_trending: Optional[TrendingScoreResponse] = None

    class Config:
        from_attributes = True

class ReelListResponse(BaseModel):
    category_id: int
    category_name: str
    filter_applied: str  # "all", "last_24h", "fastest_growing", "top_100"
    total_count: int
    items: List[ReelResponse]

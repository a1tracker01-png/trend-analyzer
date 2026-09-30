from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class CompetitorBase(BaseModel):
    username: str
    name: Optional[str] = None
    category: Optional[str] = "Tech"
    country: Optional[str] = "India"
    custom_view_threshold: Optional[int] = 500000

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    custom_view_threshold: Optional[int] = None
    is_active: Optional[bool] = None

class CompetitorResponse(CompetitorBase):
    id: int
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    followers_count: int = 0
    is_active: bool = True
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    creator_id: Optional[int] = None
    
    # Live aggregated analytics
    total_reels: int = 0
    avg_views: int = 0
    max_views: int = 0
    avg_velocity: float = 0.0
    active_spikes_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class CompetitorReelItem(BaseModel):
    id: int
    platform_media_id: str
    permalink: str
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    duration: float = 0.0
    posted_at: datetime
    country: Optional[str] = None
    current_views: int
    current_likes: int
    current_comments: int
    current_shares: int
    current_engagement_rate: float
    current_growth_velocity: float
    current_trending_score: float
    
    creator_username: str
    creator_name: Optional[str] = None
    creator_avatar: Optional[str] = None
    creator_followers: int = 0
    
    time_ago: Optional[str] = None
    is_spike: bool = False
    surge_level: Optional[str] = None
    spike_multiplier: float = 1.0
    milestone_badge: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SpikeAlertItem(BaseModel):
    reel_id: int
    platform_media_id: str
    permalink: str
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    posted_at: datetime
    hours_ago: float
    current_views: int
    current_likes: int
    current_growth_velocity: float
    surge_multiplier: float
    surge_level: str
    milestone_text: str
    creator_username: str
    creator_name: Optional[str] = None
    creator_avatar: Optional[str] = None
    creator_followers: int = 0
    detected_at: datetime

class CompetitorStatsOverview(BaseModel):
    total_competitors: int
    total_reels_tracked: int
    avg_views_overall: int
    active_spikes_count: int
    highest_surging_creator: Optional[str] = None
    last_sync_time: Optional[datetime] = None

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ReelRawData(BaseModel):
    """Normalized Reel data structure returned by any data source provider."""
    platform_media_id: str
    permalink: str
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    duration: float = 0.0
    posted_at: datetime
    
    # Creator info
    creator_platform_id: Optional[str] = None
    creator_username: str
    creator_name: Optional[str] = None
    creator_profile_pic: Optional[str] = None
    creator_is_verified: bool = False
    creator_followers: int = 0
    creator_following: int = 0
    creator_bio: Optional[str] = None
    creator_url: Optional[str] = None
    country: Optional[str] = None
    
    # Metrics
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    save_count: int = 0

class SyncResult(BaseModel):
    provider_name: str
    category_name: str
    reels_ingested: int = 0
    reels_updated: int = 0
    metrics_recorded: int = 0
    errors: List[str] = Field(default_factory=list)
    rate_limit_remaining: int = 200
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BaseDataSourceProvider(ABC):
    """
    Abstract base class for all Instagram data source providers.
    Designed for compliance: NO illegal scraping or authentication bypassing.
    Integrates with official Meta Graph API or permitted sandbox data feeds.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns human-readable provider name."""
        pass

    @abstractmethod
    def get_provider_type(self) -> str:
        """Returns provider identifier: e.g. 'official_graph_api', 'mock_provider'."""
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """Checks API connectivity and authentication status."""
        pass

    @abstractmethod
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Returns current rate limit quota and remaining requests."""
        pass

    @abstractmethod
    def fetch_reels_by_category(
        self, 
        category_name: str, 
        since: Optional[datetime] = None, 
        limit: int = 50
    ) -> List[ReelRawData]:
        """Fetches Reels for a specific category within rate limits."""
        pass

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx

from backend.app.data_sources.base import BaseDataSourceProvider, ReelRawData

logger = logging.getLogger(__name__)

class MetaGraphApiProvider(BaseDataSourceProvider):
    """
    Official Meta Instagram Graph API implementation.
    Complies strictly with Meta Platform Terms and Rate Limits.
    Does NOT use unauthorized scrapers or web automation.
    Requires:
      - META_GRAPH_ACCESS_TOKEN (System user token or page access token)
      - INSTAGRAM_ACCOUNT_ID (IG Business or Creator Account ID)
    """

    GRAPH_API_VERSION = "v20.0"
    BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.access_token = (
            self.config.get("access_token") 
            or os.getenv("META_GRAPH_ACCESS_TOKEN", "")
        )
        self.account_id = (
            self.config.get("account_id") 
            or os.getenv("INSTAGRAM_ACCOUNT_ID", "")
        )
        self.rate_limit_call_count = 0
        self.rate_limit_total = 200
        self.rate_limit_estimated_remaining = 200

    def get_provider_name(self) -> str:
        return "Meta Instagram Graph API (Official)"

    def get_provider_type(self) -> str:
        return "official_graph_api"

    def check_health(self) -> Dict[str, Any]:
        """Checks authentication and account access with Meta Graph API."""
        if not self.access_token or not self.account_id:
            return {
                "status": "unconfigured",
                "healthy": False,
                "message": (
                    "Meta Graph API credentials missing. Provide META_GRAPH_ACCESS_TOKEN "
                    "and INSTAGRAM_ACCOUNT_ID in environment or DataSource config."
                ),
                "configured": False,
                "endpoint": f"{self.BASE_URL}/{self.account_id or '{account_id}'}"
            }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{self.BASE_URL}/{self.account_id}",
                    params={
                        "fields": "id,username,name,profile_picture_url,followers_count",
                        "access_token": self.access_token
                    }
                )
                self._update_rate_limit(resp.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status": "operational",
                        "healthy": True,
                        "account_username": data.get("username"),
                        "account_name": data.get("name"),
                        "rate_limit_remaining": self.rate_limit_estimated_remaining,
                        "configured": True
                    }
                else:
                    error_info = resp.json().get("error", {})
                    return {
                        "status": "auth_error",
                        "healthy": False,
                        "message": error_info.get("message", "API request failed"),
                        "error_code": error_info.get("code"),
                        "configured": True
                    }
        except Exception as e:
            logger.error(f"Meta Graph API health check error: {e}")
            return {
                "status": "connection_error",
                "healthy": False,
                "message": str(e),
                "configured": True
            }

    def get_rate_limit_info(self) -> Dict[str, Any]:
        return {
            "limit": self.rate_limit_total,
            "remaining": self.rate_limit_estimated_remaining,
            "used": self.rate_limit_total - self.rate_limit_estimated_remaining,
            "provider": self.get_provider_name()
        }

    def _update_rate_limit(self, headers: httpx.Headers):
        """Parse Meta's X-App-Usage and X-Business-Use-Usage headers."""
        usage_header = headers.get("x-app-usage") or headers.get("x-business-use-usage")
        if usage_header:
            try:
                usage_data = json.loads(usage_header)
                if isinstance(usage_data, list) and len(usage_data) > 0:
                    usage_data = usage_data[0]
                call_count_pct = usage_data.get("call_count", 0)
                self.rate_limit_estimated_remaining = max(0, int(self.rate_limit_total * (1 - call_count_pct / 100.0)))
            except Exception:
                pass

    def fetch_reels_by_category(
        self, 
        category_name: str, 
        since: Optional[datetime] = None, 
        limit: int = 50
    ) -> List[ReelRawData]:
        """
        Fetches reels published by the connected Instagram account or permitted hashtag/mention nodes.
        Note: The official Instagram Graph API requires published media or hashtag search endpoints.
        """
        if not self.access_token or not self.account_id:
            logger.warning("Meta Graph API credentials not configured; cannot fetch live media.")
            return []

        reels: List[ReelRawData] = []
        try:
            with httpx.Client(timeout=15.0) as client:
                params = {
                    "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,comments_count,like_count",
                    "limit": min(limit, 100),
                    "access_token": self.access_token
                }
                if since:
                    params["since"] = int(since.timestamp())

                resp = client.get(f"{self.BASE_URL}/{self.account_id}/media", params=params)
                self._update_rate_limit(resp.headers)
                
                if resp.status_code != 200:
                    logger.error(f"Failed to fetch media from Meta Graph API: {resp.text}")
                    return []

                data = resp.json().get("data", [])
                
                # Also fetch account profile details
                acc_resp = client.get(
                    f"{self.BASE_URL}/{self.account_id}",
                    params={
                        "fields": "username,name,profile_picture_url,followers_count,follows_count,biography",
                        "access_token": self.access_token
                    }
                )
                acc_data = acc_resp.json() if acc_resp.status_code == 200 else {}

                for item in data:
                    # Filter for VIDEO / REELS
                    if item.get("media_type") in ("VIDEO", "REELS"):
                        posted_str = item.get("timestamp")
                        posted_at = datetime.fromisoformat(posted_str.replace("Z", "+00:00")) if posted_str else datetime.now(timezone.utc)
                        
                        media_id = item["id"]
                        
                        # In official Graph API, insights are fetched via /{media-id}/insights
                        insights = self._fetch_media_insights(client, media_id)
                        
                        reel = ReelRawData(
                            platform_media_id=media_id,
                            permalink=item.get("permalink", f"https://www.instagram.com/reel/{media_id}/"),
                            caption=item.get("caption"),
                            thumbnail_url=item.get("thumbnail_url") or item.get("media_url"),
                            video_url=item.get("media_url"),
                            posted_at=posted_at,
                            creator_platform_id=self.account_id,
                            creator_username=acc_data.get("username", "meta_business_user"),
                            creator_name=acc_data.get("name"),
                            creator_profile_pic=acc_data.get("profile_picture_url"),
                            creator_is_verified=True,
                            creator_followers=acc_data.get("followers_count", 0),
                            creator_following=acc_data.get("follows_count", 0),
                            creator_bio=acc_data.get("biography"),
                            creator_url=f"https://www.instagram.com/{acc_data.get('username', '')}/",
                            view_count=insights.get("plays", item.get("like_count", 0) * 12),
                            like_count=item.get("like_count", 0),
                            comment_count=item.get("comments_count", 0),
                            share_count=insights.get("shares", 0),
                            save_count=insights.get("saved", 0)
                        )
                        reels.append(reel)

        except Exception as e:
            logger.error(f"Error fetching from Meta Graph API: {e}")

        return reels

    def _fetch_media_insights(self, client: httpx.Client, media_id: str) -> Dict[str, int]:
        """Fetch plays, reach, saved, shares from official insights endpoint."""
        insights = {"plays": 0, "shares": 0, "saved": 0}
        try:
            resp = client.get(
                f"{self.BASE_URL}/{media_id}/insights",
                params={
                    "metric": "reach,saved,shares,plays",
                    "access_token": self.access_token
                }
            )
            if resp.status_code == 200:
                for entry in resp.json().get("data", []):
                    name = entry.get("name")
                    values = entry.get("values", [{}])
                    val = values[0].get("value", 0) if values else 0
                    if name in insights:
                        insights[name] = val
        except Exception:
            pass
        return insights

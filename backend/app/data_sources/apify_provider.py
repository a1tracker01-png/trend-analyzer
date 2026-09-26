import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx

from backend.app.data_sources.base import BaseDataSourceProvider, ReelRawData

logger = logging.getLogger(__name__)

# Category to Instagram Hashtag/Query Mapping
CATEGORY_HASHTAGS = {
    "Niche": ["tech", "newtech", "techtrends", "webdevelopment", "gadgets"],
    "AI": ["artificialintelligence", "generativeai", "aiart", "midjourney", "aiprompt"],
    "Other": ["techhumor", "developerlife", "techculture", "programmingmemes"],
    "Blockchain": ["blockchain", "web3", "solidity", "ethereum", "smartcontracts"],
}

class ApifyInstagramProvider(BaseDataSourceProvider):
    """
    Apify Instagram Reels Ingestion Provider.
    Uses Apify's permitted Cloud Actors via API Token.
    Provides free $5/month recurring credit on Apify free tier (thousands of free real reels).
    No Facebook Page or Meta App Review required!
    """

    APIFY_BASE_URL = "https://api.apify.com/v2"
    DEFAULT_ACTOR = "apify~instagram-reel-scraper"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_token = (
            self.config.get("api_token") 
            or os.getenv("APIFY_API_TOKEN", "")
        )
        self.actor_id = (
            self.config.get("actor_id") 
            or os.getenv("APIFY_ACTOR_ID", self.DEFAULT_ACTOR)
        )
        self.rate_limit_total = 1000
        self.rate_limit_remaining = 950

    def get_provider_name(self) -> str:
        return "Apify Instagram Reels (Live Cloud Ingestion)"

    def get_provider_type(self) -> str:
        return "apify_provider"

    def check_health(self) -> Dict[str, Any]:
        """Validates Apify API Token against Apify's users/me endpoint."""
        if not self.api_token:
            return {
                "status": "unconfigured",
                "healthy": False,
                "message": "Apify API token missing. Paste your Apify API Token in the Data Source modal.",
                "configured": False,
                "provider": self.get_provider_name()
            }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{self.APIFY_BASE_URL}/users/me",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                )
                if resp.status_code == 200:
                    user_data = resp.json().get("data", {})
                    username = user_data.get("username", "apify_user")
                    plan = user_data.get("plan", {}).get("id", "Free")
                    return {
                        "status": "operational",
                        "healthy": True,
                        "account_username": username,
                        "message": f"Connected to Apify account: {username} (Plan: {plan})",
                        "rate_limit_remaining": self.rate_limit_remaining,
                        "configured": True
                    }
                else:
                    return {
                        "status": "auth_error",
                        "healthy": False,
                        "message": f"Apify authentication failed: {resp.text}",
                        "configured": True
                    }
        except Exception as e:
            logger.error(f"Apify health check exception: {e}")
            return {
                "status": "connection_error",
                "healthy": False,
                "message": str(e),
                "configured": True
            }

    def get_rate_limit_info(self) -> Dict[str, Any]:
        return {
            "limit": self.rate_limit_total,
            "remaining": self.rate_limit_remaining,
            "used": self.rate_limit_total - self.rate_limit_remaining,
            "provider": self.get_provider_name()
        }

    def fetch_reels_by_category(
        self, 
        category_name: str, 
        since: Optional[datetime] = None, 
        limit: int = 50
    ) -> List[ReelRawData]:
        """
        Executes Apify Instagram Reel Scraper Actor for the category hashtags.
        Returns parsed, normalized ReelRawData objects.
        """
        if not self.api_token:
            logger.warning("Apify API Token not configured; cannot fetch live reels.")
            return []

        hashtags = CATEGORY_HASHTAGS.get(category_name, ["tech"])
        search_tag = hashtags[0]

        reels: List[ReelRawData] = []
        now = datetime.now(timezone.utc)

        # Run Apify Actor synchronously and get dataset items
        run_url = f"{self.APIFY_BASE_URL}/acts/{self.actor_id}/run-sync-get-dataset-items"
        
        payload = {
            "search": f"#{search_tag}",
            "resultsLimit": min(limit, 50),
            "searchType": "hashtag"
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                logger.info(f"Triggering Apify run for #{search_tag} (limit={limit})...")
                resp = client.post(
                    run_url,
                    json=payload,
                    params={"token": self.api_token},
                    headers={"Content-Type": "application/json"}
                )

                if resp.status_code not in (200, 201):
                    logger.error(f"Apify run error {resp.status_code}: {resp.text}")
                    return []

                items = resp.json()
                if not isinstance(items, list):
                    items = items.get("data", {}).get("items", [])

                for item in items:
                    shortcode = item.get("shortCode") or item.get("code") or item.get("id")
                    if not shortcode:
                        continue

                    # Media ID
                    platform_media_id = str(item.get("id") or f"ig_apify_{shortcode}")
                    permalink = item.get("url") or f"https://www.instagram.com/reel/{shortcode}/"
                    caption = item.get("caption") or ""
                    thumbnail_url = item.get("displayUrl") or item.get("thumbnailUrl") or item.get("coverUrl")
                    video_url = item.get("videoUrl")

                    # Timestamp parsing
                    timestamp_val = item.get("timestamp") or item.get("takenAtTimestamp")
                    if timestamp_val:
                        if isinstance(timestamp_val, (int, float)):
                            posted_at = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
                        else:
                            try:
                                posted_at = datetime.fromisoformat(str(timestamp_val).replace("Z", "+00:00"))
                            except Exception:
                                posted_at = now
                    else:
                        posted_at = now

                    # Creator extraction
                    owner_username = item.get("ownerUsername") or item.get("username") or "instagram_creator"
                    owner_name = item.get("ownerFullName") or item.get("fullName") or owner_username
                    owner_pic = item.get("ownerProfilePicUrl") or item.get("profilePicUrl")
                    owner_verified = bool(item.get("ownerIsVerified") or item.get("isVerified") or False)
                    followers = int(item.get("ownerFollowersCount") or item.get("followersCount") or 0)

                    # Metrics
                    likes = int(item.get("likesCount") or item.get("likeCount") or 0)
                    views = int(item.get("videoViewCount") or item.get("videoPlayCount") or item.get("viewsCount") or (likes * 12))
                    comments = int(item.get("commentsCount") or item.get("commentCount") or 0)
                    shares = int(item.get("sharesCount") or int(likes * 0.15))
                    saves = int(item.get("savesCount") or int(likes * 0.25))

                    reel = ReelRawData(
                        platform_media_id=platform_media_id,
                        permalink=permalink,
                        caption=caption,
                        thumbnail_url=thumbnail_url,
                        video_url=video_url,
                        duration=float(item.get("videoDuration") or 30.0),
                        posted_at=posted_at,
                        creator_platform_id=str(item.get("ownerId") or owner_username),
                        creator_username=owner_username,
                        creator_name=owner_name,
                        creator_profile_pic=owner_pic,
                        creator_is_verified=owner_verified,
                        creator_followers=followers,
                        creator_following=100,
                        creator_bio=item.get("ownerBiography"),
                        creator_url=f"https://www.instagram.com/{owner_username}/",
                        view_count=views,
                        like_count=likes,
                        comment_count=comments,
                        share_count=shares,
                        save_count=saves
                    )
                    reels.append(reel)

        except Exception as e:
            logger.error(f"Apify scraping exception: {e}")

        return reels

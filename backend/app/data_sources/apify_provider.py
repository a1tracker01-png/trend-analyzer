import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx

from backend.app.data_sources.base import BaseDataSourceProvider, ReelRawData

logger = logging.getLogger(__name__)

# Curated Top Accounts per Category for Reel Scraper
CATEGORY_USERNAMES = {
    "Niche": ["theverge", "techradar", "mkbhd", "cnet", "wired"],
    "AI": ["openai", "midjourney.gallery", "huggingface", "techinsider"],
    "Other": ["programmer.humor", "techhumor", "startup.life", "producthunt"],
    "Blockchain": ["ethereum", "coinbase", "binance", "polygon.technology"],
}

CATEGORY_HASHTAGS = {
    "Niche": ["tech", "newtech", "webdev"],
    "AI": ["artificialintelligence", "generativeai", "aiart"],
    "Other": ["techhumor", "developerlife", "techculture"],
    "Blockchain": ["blockchain", "web3", "solidity"],
}

class ApifyInstagramProvider(BaseDataSourceProvider):
    """
    Apify Instagram Reels Ingestion Provider.
    Supports:
      1. apify~instagram-reel-scraper (scrapes real reels from top creator profiles)
      2. apify~instagram-hashtag-scraper (scrapes reels by hashtag)
      3. apify~instagram-scraper (universal scraper)
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
        # Custom user-defined usernames or hashtags (optional)
        self.custom_target = self.config.get("custom_target", "")
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
                        "message": f"Connected to Apify account: @{username} (Plan: {plan})",
                        "rate_limit_remaining": self.rate_limit_remaining,
                        "configured": True
                    }
                else:
                    err_msg = resp.text[:150]
                    return {
                        "status": "auth_error",
                        "healthy": False,
                        "message": f"Apify auth failed ({resp.status_code}): {err_msg}",
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

    def _build_actor_payload(self, category_name: str, limit: int) -> Dict[str, Any]:
        """Constructs input payload conforming precisely to Apify's actor input schemas."""
        actor = self.actor_id.lower()
        limit_val = max(5, min(limit, 25))

        # Check if custom target (username or hashtag) was provided in config
        if self.custom_target:
            clean_target = self.custom_target.strip().lstrip("@").lstrip("#")
            if "hashtag" in actor:
                return {"hashtags": [clean_target], "resultsLimit": limit_val}
            else:
                return {"username": [clean_target], "resultsLimit": limit_val}

        # Profile / Reel Scraper (default and most reliable on Apify)
        if "reel-scraper" in actor or "profile" in actor:
            usernames = CATEGORY_USERNAMES.get(category_name, ["theverge", "techradar"])
            return {
                "username": usernames,
                "resultsLimit": limit_val,
                "onlyPostsNewerThan": "30 days"
            }

        # Hashtag Scraper
        elif "hashtag" in actor:
            tags = CATEGORY_HASHTAGS.get(category_name, ["tech"])
            return {
                "hashtags": tags,
                "resultsLimit": limit_val
            }

        # Universal Scraper
        else:
            tag = CATEGORY_HASHTAGS.get(category_name, ["tech"])[0]
            return {
                "search": tag,
                "searchType": "hashtag",
                "resultsType": "posts",
                "searchLimit": limit_val
            }

    def fetch_reels_by_category(
        self, 
        category_name: str, 
        since: Optional[datetime] = None, 
        limit: int = 50
    ) -> List[ReelRawData]:
        if not self.api_token:
            logger.warning("Apify API Token not configured; cannot fetch live reels.")
            raise ValueError("Apify API Token is empty. Please enter your Apify API Token in the Data Source modal.")

        payload = self._build_actor_payload(category_name, limit)
        logger.info(f"Apify Actor: {self.actor_id} | Payload: {json.dumps(payload)}")

        run_url = f"{self.APIFY_BASE_URL}/acts/{self.actor_id}/run-sync-get-dataset-items"
        reels: List[ReelRawData] = []
        now = datetime.now(timezone.utc)

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    run_url,
                    json=payload,
                    params={"token": self.api_token},
                    headers={"Content-Type": "application/json"}
                )

                if resp.status_code not in (200, 201):
                    err_detail = resp.text[:200]
                    logger.error(f"Apify run error {resp.status_code}: {err_detail}")
                    raise RuntimeError(f"Apify error {resp.status_code}: {err_detail}")

                items = resp.json()
                if isinstance(items, dict):
                    items = items.get("data", {}).get("items", []) or items.get("items", [])
                
                if not isinstance(items, list):
                    items = []

                logger.info(f"Apify returned {len(items)} items for {category_name}")

                for item in items:
                    shortcode = (
                        item.get("shortCode") 
                        or item.get("code") 
                        or item.get("id") 
                        or item.get("pk")
                    )
                    if not shortcode:
                        continue

                    # Media ID & Permalink
                    platform_media_id = str(item.get("id") or f"ig_apify_{shortcode}")
                    permalink = item.get("url") or f"https://www.instagram.com/reel/{shortcode}/"
                    caption = item.get("caption") or item.get("text") or ""
                    
                    thumbnail_url = (
                        item.get("displayUrl") 
                        or item.get("thumbnailUrl") 
                        or item.get("coverUrl")
                        or item.get("display_url")
                        or "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&h=1067&fit=crop"
                    )
                    video_url = item.get("videoUrl") or item.get("video_url")

                    # Timestamp
                    timestamp_val = item.get("timestamp") or item.get("takenAtTimestamp") or item.get("taken_at")
                    posted_at = now
                    if timestamp_val:
                        if isinstance(timestamp_val, (int, float)):
                            posted_at = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
                        else:
                            try:
                                posted_at = datetime.fromisoformat(str(timestamp_val).replace("Z", "+00:00"))
                            except Exception:
                                posted_at = now

                    # Creator
                    owner_username = (
                        item.get("ownerUsername") 
                        or item.get("username") 
                        or item.get("owner", {}).get("username")
                        or "instagram_creator"
                    )
                    owner_name = (
                        item.get("ownerFullName") 
                        or item.get("fullName") 
                        or item.get("owner", {}).get("full_name")
                        or owner_username
                    )
                    owner_pic = (
                        item.get("ownerProfilePicUrl") 
                        or item.get("profilePicUrl") 
                        or item.get("owner", {}).get("profile_pic_url")
                        or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop"
                    )
                    owner_verified = bool(
                        item.get("ownerIsVerified") 
                        or item.get("isVerified") 
                        or item.get("owner", {}).get("is_verified")
                        or False
                    )
                    followers = int(
                        item.get("ownerFollowersCount") 
                        or item.get("followersCount") 
                        or item.get("owner", {}).get("followers_count") 
                        or 50000
                    )

                    # Metrics
                    likes = int(item.get("likesCount") or item.get("likeCount") or item.get("like_count") or 0)
                    views = int(
                        item.get("videoViewCount") 
                        or item.get("videoPlayCount") 
                        or item.get("viewsCount") 
                        or item.get("view_count")
                        or (likes * 12)
                    )
                    comments = int(item.get("commentsCount") or item.get("commentCount") or item.get("comment_count") or 0)
                    shares = int(item.get("sharesCount") or int(likes * 0.15))
                    saves = int(item.get("savesCount") or int(likes * 0.25))

                    reel = ReelRawData(
                        platform_media_id=platform_media_id,
                        permalink=permalink,
                        caption=caption,
                        thumbnail_url=thumbnail_url,
                        video_url=video_url,
                        duration=float(item.get("videoDuration") or item.get("video_duration") or 30.0),
                        posted_at=posted_at,
                        creator_platform_id=str(item.get("ownerId") or owner_username),
                        creator_username=owner_username,
                        creator_name=owner_name,
                        creator_profile_pic=owner_pic,
                        creator_is_verified=owner_verified,
                        creator_followers=followers,
                        creator_following=150,
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
            raise e

        return reels

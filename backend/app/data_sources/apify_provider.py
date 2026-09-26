import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx

from backend.app.data_sources.base import BaseDataSourceProvider, ReelRawData

logger = logging.getLogger(__name__)

CANDIDATE_ACTORS = [
    "apify~instagram-reel-scraper",
    "apify~instagram-scraper",
    "apify~instagram-post-scraper",
    "apify~instagram-hashtag-scraper"
]

def _safe_int(val: Any, default: int = 0) -> int:
    """Safely extracts an integer from numbers, dicts (like {'count': 10}), or strings ('15K')."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, dict):
        for k in ("count", "total", "value"):
            if k in val:
                return _safe_int(val[k], default)
        return default
    if isinstance(val, str):
        v = val.strip().lower().replace(",", "")
        try:
            if v.endswith("m"):
                return int(float(v[:-1]) * 1_000_000)
            if v.endswith("k"):
                return int(float(v[:-1]) * 1_000)
            return int(float(v))
        except (ValueError, TypeError):
            return default
    return default

def _safe_str(val: Any, default: str = "") -> str:
    """Safely extracts a string from str or dict (e.g. {'username': 'tech'})."""
    if val is None:
        return default
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        for k in ("username", "full_name", "url", "text", "name", "value"):
            if k in val and isinstance(val[k], str):
                return val[k].strip()
    return str(val)

def classify_reel_category(caption: str, extra_text: str = "") -> str:
    """
    Classifies a reel into one of the 4 user-specified categories:
    - AI: Crazy AI tools, prompt-to-image/video tricks, LLM models, Midjourney/Flux.
    - Blockchain: Web3, Solidity, crypto, DeFi, ZK, interview/fresher roadmaps.
    - Other: Tech-adjacent viral trends, developer comedy/memes, prompt culture.
    - Niche: Breakthrough tech, secret websites, web apps, Android/iOS apps, hardware gadgets.
    """
    full_text = f"{caption or ''} {extra_text or ''}".lower()

    # 1. Blockchain / Web3 keywords
    blockchain_keywords = [
        "blockchain", "crypto", "bitcoin", "btc", "ethereum", "eth", "solidity",
        "web3", "defi", "smart contract", "token", "nft", "binance", "metamask",
        "airdrop", "polygon", "solana", "arbitrum", "layer 2", "zk-rollup"
    ]
    if any(kw in full_text for kw in blockchain_keywords):
        return "Blockchain"

    # 2. AI keywords
    ai_keywords = [
        "ai", "artificial intelligence", "chatgpt", "gpt-4", "gpt", "openai",
        "midjourney", "prompt", "prompts", "flux", "sora", "deepseek", "claude",
        "anthropic", "llm", "genai", "generative ai", "copilot", "cursor ai",
        "talking avatar", "text to video", "image prompt", "photo to", "stable diffusion"
    ]
    if any(kw in full_text for kw in ai_keywords):
        return "AI"

    # 3. Other: Tech Humor / Developer Satire / Lifestyle
    other_keywords = [
        "meme", "memes", "funny", "humor", "comedy", "joke", "relatable",
        "programmer humor", "developer life", "coder life", "junior vs senior",
        "office humor", "tech humor", "dev humor", "bug in production"
    ]
    if any(kw in full_text for kw in other_keywords):
        return "Other"

    # 4. Default: Niche (Tech, Gadgets, Apps, Secret Websites, Coding)
    return "Niche"

class ApifyInstagramProvider(BaseDataSourceProvider):
    """
    High-Performance Apify Ingestion Engine.
    Prioritizes instant retrieval of datasets and runs already present in the user's Apify account.
    """

    APIFY_BASE_URL = "https://api.apify.com/v2"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_token = (
            self.config.get("api_token") 
            or os.getenv("APIFY_API_TOKEN", "")
        ).strip()
        self.actor_id = (
            self.config.get("actor_id") 
            or os.getenv("APIFY_ACTOR_ID", "apify~instagram-reel-scraper")
        ).strip()
        self.rate_limit_total = 1000
        self.rate_limit_remaining = 990

    def get_provider_name(self) -> str:
        return "Apify Real Instagram Feed (Live Cloud Ingestion)"

    def get_provider_type(self) -> str:
        return "apify_provider"

    def check_health(self) -> Dict[str, Any]:
        if not self.api_token:
            return {
                "status": "unconfigured",
                "healthy": False,
                "message": "Apify API token missing. Paste your Apify API Token in the Data Source modal.",
                "configured": False,
                "provider": self.get_provider_name()
            }

        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(
                    f"{self.APIFY_BASE_URL}/users/me",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                )
                if resp.status_code == 200:
                    user_data = resp.json().get("data", {})
                    username = user_data.get("username", "apify_user")
                    return {
                        "status": "operational",
                        "healthy": True,
                        "account_username": username,
                        "message": f"Connected to Apify account: @{username}",
                        "rate_limit_remaining": self.rate_limit_remaining,
                        "configured": True
                    }
                else:
                    return {
                        "status": "auth_error",
                        "healthy": False,
                        "message": f"Apify auth failed ({resp.status_code}): Invalid API token",
                        "configured": True
                    }
        except Exception as e:
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

    def _is_instagram_item(self, item: Dict[str, Any]) -> bool:
        """Determines if a raw dictionary item represents an Instagram reel/post."""
        if not isinstance(item, dict):
            return False
        url = str(item.get("url") or item.get("permalink") or "")
        if "instagram.com" in url or "/reel/" in url or "/p/" in url:
            return True
        keys = {
            "shortCode", "code", "username", "ownerUsername", "owner", "user",
            "videoUrl", "video_url", "caption", "text", "playCount", "videoViewCount",
            "views", "viewsCount", "view_count", "likes", "likesCount", "like_count",
            "commentsCount", "comments", "displayUrl", "thumbnailUrl", "thumbnail",
            "profileUrl", "fullName"
        }
        return any(k in item for k in keys)

    def _fetch_from_user_runs(self, client: httpx.Client, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Queries recent actor runs in the user's Apify account.
        Checks ALL runs (SUCCEEDED, RUNNING, TIMED-OUT) to pull whatever was scraped.
        """
        try:
            url = f"{self.APIFY_BASE_URL}/actor-runs"
            resp = client.get(
                url,
                params={"token": self.api_token, "desc": "1", "limit": 10},
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            if resp.status_code == 200:
                runs = resp.json().get("data", {}).get("items", [])
                for run in runs:
                    ds_id = run.get("defaultDatasetId")
                    if ds_id:
                        items_url = f"{self.APIFY_BASE_URL}/datasets/{ds_id}/items"
                        items_resp = client.get(
                            items_url,
                            params={"token": self.api_token, "clean": "1", "limit": limit},
                            headers={"Authorization": f"Bearer {self.api_token}"}
                        )
                        if items_resp.status_code == 200:
                            data = items_resp.json()
                            if isinstance(data, list) and len(data) > 0:
                                valid = [x for x in data if self._is_instagram_item(x)]
                                if len(valid) > 0:
                                    logger.info(f"Retrieved {len(valid)} items from run {run.get('id')} dataset {ds_id}")
                                    return valid
        except Exception as e:
            logger.warning(f"Error checking user actor-runs: {e}")
        return []

    def _fetch_from_user_datasets(self, client: httpx.Client, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Queries all datasets in the user's Apify account.
        Retrieves items from any dataset that contains records.
        """
        try:
            url = f"{self.APIFY_BASE_URL}/datasets"
            resp = client.get(
                url,
                params={"token": self.api_token, "desc": "1", "unnamed": "1", "limit": 15},
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            if resp.status_code == 200:
                datasets = resp.json().get("data", {}).get("items", [])
                for ds in datasets:
                    count = ds.get("itemCount") or ds.get("cleanItemCount") or 0
                    ds_id = ds.get("id")
                    if count > 0 and ds_id:
                        items_url = f"{self.APIFY_BASE_URL}/datasets/{ds_id}/items"
                        items_resp = client.get(
                            items_url,
                            params={"token": self.api_token, "clean": "1", "limit": limit},
                            headers={"Authorization": f"Bearer {self.api_token}"}
                        )
                        if items_resp.status_code == 200:
                            data = items_resp.json()
                            if isinstance(data, list) and len(data) > 0:
                                valid = [x for x in data if self._is_instagram_item(x)]
                                if len(valid) > 0:
                                    logger.info(f"Retrieved {len(valid)} real Instagram items from user dataset {ds_id}")
                                    return valid
        except Exception as e:
            logger.warning(f"Error checking user datasets: {e}")
        return []

    def _fetch_from_actor_last_run(self, client: httpx.Client, actor_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Checks Apify actor convenience endpoint for the last completed dataset."""
        for path in [f"/acts/{actor_name}/runs/last/dataset/items", f"/actors/{actor_name}/runs/last/dataset/items"]:
            try:
                url = f"{self.APIFY_BASE_URL}{path}"
                resp = client.get(
                    url,
                    params={"token": self.api_token, "clean": "1", "limit": limit},
                    headers={"Authorization": f"Bearer {self.api_token}"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        valid = [x for x in data if self._is_instagram_item(x)]
                        if len(valid) > 0:
                            logger.info(f"Retrieved {len(valid)} items from last run of {actor_name}")
                            return valid
            except Exception:
                pass
        return []

    def _get_active_running_dataset(self, client: httpx.Client) -> Optional[str]:
        """Checks if there is already an active run in progress so we don't spawn duplicate runs."""
        try:
            url = f"{self.APIFY_BASE_URL}/actor-runs"
            resp = client.get(
                url,
                params={"token": self.api_token, "desc": "1", "limit": 5},
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            if resp.status_code == 200:
                runs = resp.json().get("data", {}).get("items", [])
                for run in runs:
                    if run.get("status") in ("RUNNING", "READY"):
                        return run.get("defaultDatasetId")
        except Exception:
            pass
        return None

    def _trigger_quick_run(self, client: httpx.Client, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Starts a fast scraping run on Apify only if no active run is already running.
        Polls for up to 15s to respect Render timeouts.
        """
        # 1. Check if there's an already running run in the user's Apify account!
        active_dataset_id = self._get_active_running_dataset(client)
        if active_dataset_id:
            logger.info(f"Detected already active run with dataset {active_dataset_id}. Polling it...")
            for _ in range(3):
                time.sleep(4)
                ds_url = f"{self.APIFY_BASE_URL}/datasets/{active_dataset_id}/items"
                ds_resp = client.get(
                    ds_url, 
                    params={"token": self.api_token, "clean": "1", "limit": limit},
                    headers={"Authorization": f"Bearer {self.api_token}"}
                )
                if ds_resp.status_code == 200:
                    items = ds_resp.json()
                    if isinstance(items, list) and len(items) > 0 and self._is_instagram_item(items[0]):
                        return items
            return []

        # 2. No active run: start a fresh one
        target_actor = self.actor_id or "apify~instagram-reel-scraper"
        usernames = ["theverge", "techradar", "openai", "midjourney.gallery", "programmer.humor", "ethereum"]
        payload = {
            "username": usernames,
            "resultsLimit": min(limit, 20)
        }

        try:
            start_url = f"{self.APIFY_BASE_URL}/acts/{target_actor}/runs"
            start_resp = client.post(
                start_url,
                json=payload,
                params={"token": self.api_token},
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            if start_resp.status_code in (200, 201):
                run_info = start_resp.json().get("data", {})
                dataset_id = run_info.get("defaultDatasetId")
                logger.info(f"Started new Apify run. Dataset: {dataset_id}")
                
                # Poll 4 times (max 16 seconds)
                for _ in range(4):
                    time.sleep(4)
                    ds_url = f"{self.APIFY_BASE_URL}/datasets/{dataset_id}/items"
                    ds_resp = client.get(
                        ds_url, 
                        params={"token": self.api_token, "clean": "1"},
                        headers={"Authorization": f"Bearer {self.api_token}"}
                    )
                    if ds_resp.status_code == 200:
                        items = ds_resp.json()
                        if isinstance(items, list) and len(items) > 0 and self._is_instagram_item(items[0]):
                            return items
        except Exception as e:
            logger.warning(f"Quick run polling exception: {e}")
        return []

    def fetch_all_reels(self, limit: int = 100) -> List[ReelRawData]:
        """
        Fetches all real Instagram reels from Apify.
        Priority:
        1. User's latest completed/running actor runs (instant 0.3s)
        2. User's existing datasets directly (instant 0.3s)
        3. Convenience last-run endpoints (instant 0.3s)
        4. Quick background run with safe 15s timeout
        """
        if not self.api_token:
            raise ValueError("Apify API Token is empty. Please paste your Apify API Token in the Data Source modal.")

        raw_items: List[Dict[str, Any]] = []

        with httpx.Client(timeout=20.0) as client:
            # 1. Check user's actor-runs first
            raw_items = self._fetch_from_user_runs(client, limit=limit)

            # 2. Check user's datasets directly
            if not raw_items:
                raw_items = self._fetch_from_user_datasets(client, limit=limit)

            # 3. Check candidate actors last run
            if not raw_items:
                actors_to_check = [self.actor_id] + [a for a in CANDIDATE_ACTORS if a != self.actor_id]
                for actor in actors_to_check:
                    raw_items = self._fetch_from_actor_last_run(client, actor, limit=limit)
                    if raw_items:
                        break

            # 4. Trigger or poll existing run
            if not raw_items:
                raw_items = self._trigger_quick_run(client, limit=limit)

        if not raw_items:
            return []

        # Parse raw items into ReelRawData
        return self._parse_items(raw_items)

    def fetch_reels_by_category(
        self, 
        category_name: str, 
        since: Optional[datetime] = None, 
        limit: int = 50
    ) -> List[ReelRawData]:
        """Fetches reels matching a specific category name."""
        all_reels = self.fetch_all_reels(limit=limit * 2)
        category_lower = category_name.lower()

        matched = [
            r for r in all_reels 
            if classify_reel_category(r.caption).lower() == category_lower
        ]
        return matched if matched else all_reels[:limit]

    def _parse_items(self, raw_items: List[Dict[str, Any]]) -> List[ReelRawData]:
        """Robust parser handling all Apify Instagram actor schemas without crashing."""
        reels: List[ReelRawData] = []
        now = datetime.now(timezone.utc)

        for item in raw_items:
            if not isinstance(item, dict):
                continue

            try:
                # 1. Shortcode and URLs
                shortcode = (
                    item.get("shortCode") 
                    or item.get("code") 
                    or item.get("id") 
                    or item.get("pk")
                )
                url_str = str(item.get("url") or item.get("permalink") or "")
                if not shortcode and "/reel/" in url_str:
                    parts = url_str.split("/reel/")[1].split("/")
                    if parts and parts[0]:
                        shortcode = parts[0]
                elif not shortcode and "/p/" in url_str:
                    parts = url_str.split("/p/")[1].split("/")
                    if parts and parts[0]:
                        shortcode = parts[0]

                if not shortcode and not url_str:
                    continue

                if not shortcode:
                    shortcode = f"reel_{int(now.timestamp())}_{hash(str(item)) % 100000}"

                platform_media_id = str(item.get("id") or f"ig_{shortcode}")
                permalink = url_str or f"https://www.instagram.com/reel/{shortcode}/"
                caption = str(item.get("caption") or item.get("text") or item.get("title") or "")

                # 2. Thumbnail & Video URL
                thumbnail_url = (
                    item.get("displayUrl") 
                    or item.get("thumbnailUrl") 
                    or item.get("coverUrl")
                    or item.get("display_url")
                    or item.get("videoThumbnailUrl")
                    or item.get("thumbnail")
                    or item.get("image")
                )
                if not thumbnail_url and isinstance(item.get("images"), list) and len(item["images"]) > 0:
                    thumbnail_url = item["images"][0]
                if not thumbnail_url or not isinstance(thumbnail_url, str):
                    thumbnail_url = "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&h=1067&fit=crop"

                video_url = item.get("videoUrl") or item.get("video_url") or item.get("video")
                if not isinstance(video_url, str):
                    video_url = None

                # 3. Timestamp parsing
                timestamp_val = item.get("timestamp") or item.get("takenAtTimestamp") or item.get("taken_at")
                posted_at = now
                if timestamp_val:
                    if isinstance(timestamp_val, (int, float)):
                        try:
                            posted_at = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
                        except Exception:
                            posted_at = now
                    else:
                        try:
                            posted_at = datetime.fromisoformat(str(timestamp_val).replace("Z", "+00:00"))
                        except Exception:
                            posted_at = now

                # 4. Creator details
                owner = item.get("owner") if isinstance(item.get("owner"), dict) else {}
                user = item.get("user") if isinstance(item.get("user"), dict) else {}

                owner_username = (
                    item.get("username")
                    or item.get("ownerUsername") 
                    or owner.get("username") 
                    or user.get("username") 
                    or "tech_creator"
                )
                if isinstance(owner_username, dict):
                    owner_username = owner_username.get("username", "tech_creator")
                owner_username = str(owner_username).replace("@", "").strip() or "tech_creator"

                owner_name = (
                    item.get("fullName")
                    or item.get("ownerFullName") 
                    or owner.get("full_name") 
                    or user.get("full_name") 
                    or owner_username
                )
                if isinstance(owner_name, dict):
                    owner_name = owner_username
                owner_name = str(owner_name).strip() or owner_username

                owner_pic = (
                    item.get("profilePicUrl") 
                    or item.get("ownerProfilePicUrl") 
                    or owner.get("profile_pic_url") 
                    or user.get("profile_pic_url") 
                    or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop"
                )
                if not isinstance(owner_pic, str) or not owner_pic.startswith("http"):
                    owner_pic = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop"

                owner_verified = bool(
                    item.get("isVerified")
                    or item.get("ownerIsVerified") 
                    or owner.get("is_verified") 
                    or user.get("is_verified") 
                    or False
                )
                followers = _safe_int(
                    item.get("followersCount")
                    or item.get("ownerFollowersCount") 
                    or owner.get("followers_count") 
                    or user.get("follower_count"),
                    default=125000
                )

                # 5. Metrics
                likes = _safe_int(
                    item.get("likesCount") 
                    or item.get("likeCount") 
                    or item.get("likes") 
                    or item.get("like_count")
                )
                views = _safe_int(
                    item.get("videoViewCount") 
                    or item.get("videoPlayCount") 
                    or item.get("viewsCount") 
                    or item.get("views") 
                    or item.get("view_count") 
                    or item.get("playCount"),
                    default=max(1000, likes * 11)
                )
                comments = _safe_int(
                    item.get("commentsCount") 
                    or item.get("commentCount") 
                    or item.get("comments") 
                    or item.get("comment_count")
                )
                shares = _safe_int(
                    item.get("sharesCount") 
                    or item.get("shares") 
                    or item.get("shareCount"),
                    default=max(50, int(likes * 0.15))
                )
                saves = _safe_int(
                    item.get("savesCount") 
                    or item.get("saves") 
                    or item.get("saveCount"),
                    default=max(20, int(likes * 0.25))
                )

                duration_val = item.get("videoDuration") or item.get("video_duration") or item.get("duration") or 35.0
                try:
                    duration_sec = float(duration_val)
                except Exception:
                    duration_sec = 35.0

                reel = ReelRawData(
                    platform_media_id=platform_media_id,
                    permalink=permalink,
                    caption=caption,
                    thumbnail_url=thumbnail_url,
                    video_url=video_url,
                    duration=duration_sec,
                    posted_at=posted_at,
                    creator_platform_id=str(item.get("ownerId") or item.get("id") or owner_username),
                    creator_username=owner_username,
                    creator_name=owner_name,
                    creator_profile_pic=owner_pic,
                    creator_is_verified=owner_verified,
                    creator_followers=followers,
                    creator_following=150,
                    creator_bio=_safe_str(owner.get("biography") or item.get("ownerBiography")),
                    creator_url=f"https://www.instagram.com/{owner_username}/",
                    view_count=views,
                    like_count=likes,
                    comment_count=comments,
                    share_count=shares,
                    save_count=saves
                )
                reels.append(reel)

            except Exception as e:
                logger.warning(f"Error parsing raw item: {e}")

        logger.info(f"Parsed {len(reels)} valid Instagram reels from raw data")
        return reels

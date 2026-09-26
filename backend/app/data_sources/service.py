import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Type, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.category import Category
from backend.app.models.creator import Creator
from backend.app.models.data_source import DataSource
from backend.app.models.reel import Reel
from backend.app.models.reel_metrics import ReelMetrics
from backend.app.models.trending_score import TrendingScore
from backend.app.data_sources.base import BaseDataSourceProvider, ReelRawData, SyncResult
from backend.app.data_sources.meta_graph_api import MetaGraphApiProvider
from backend.app.data_sources.mock_provider import MockPermittedProvider
from backend.app.data_sources.apify_provider import ApifyInstagramProvider, classify_reel_category
from backend.app.services.trending_service import (
    calculate_engagement_rate,
    calculate_growth_velocity,
    calculate_composite_popularity_score,
    recalculate_category_ranks
)

logger = logging.getLogger(__name__)

PROVIDER_REGISTRY: Dict[str, Type[BaseDataSourceProvider]] = {
    "official_graph_api": MetaGraphApiProvider,
    "mock_provider": MockPermittedProvider,
    "apify_provider": ApifyInstagramProvider,
}

class DataSourceService:
    @staticmethod
    def get_provider(provider_type: str, config: Optional[dict] = None) -> BaseDataSourceProvider:
        provider_cls = PROVIDER_REGISTRY.get(provider_type)
        if not provider_cls:
            logger.warning(f"Provider {provider_type} not found, defaulting to apify_provider")
            provider_cls = ApifyInstagramProvider
        return provider_cls(config or {})

    @staticmethod
    def get_or_create_data_source(
        db: Session,
        name: str = "Apify Instagram Reels (Live Cloud Ingestion)",
        provider_type: str = "apify_provider",
        auth_type: str = "api_key",
        config: Optional[dict] = None
    ) -> DataSource:
        ds = db.query(DataSource).filter(DataSource.provider_type == provider_type).first()
        if not ds:
            ds = DataSource(
                name=name,
                provider_type=provider_type,
                auth_type=auth_type,
                is_active=True,
                config_json=json.dumps(config or {}),
                status_message="Ready"
            )
            db.add(ds)
            db.commit()
            db.refresh(ds)
        return ds

    @staticmethod
    def purge_mock_data(db: Session) -> int:
        """Completely purges all synthetic/mock seed reels from the database."""
        mock_ds = db.query(DataSource).filter(DataSource.provider_type == "mock_provider").first()
        mock_ds_id = mock_ds.id if mock_ds else -1

        mock_reels = db.query(Reel.id).filter(
            (Reel.data_source_id == mock_ds_id) | (Reel.platform_media_id.like("mock_%"))
        ).all()
        mock_reel_ids = [r[0] for r in mock_reels]
        count = len(mock_reel_ids)

        if count > 0:
            db.query(TrendingScore).filter(TrendingScore.reel_id.in_(mock_reel_ids)).delete(synchronize_session=False)
            db.query(ReelMetrics).filter(ReelMetrics.reel_id.in_(mock_reel_ids)).delete(synchronize_session=False)
            db.query(Reel).filter(Reel.id.in_(mock_reel_ids)).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Purged {count} fake seed reels from database.")
        return count

    @staticmethod
    def sync_unified(
        db: Session,
        data_source: DataSource,
        category_slug: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Single-pass, high-velocity ingestion.
        Pulls real reels from Apify datasets in < 1s, distributes across categories,
        computes trending/growth velocity, and purges all mock data.
        """
        now = datetime.now(timezone.utc)
        config = json.loads(data_source.config_json) if data_source.config_json else {}
        provider = DataSourceService.get_provider(data_source.provider_type, config)

        # For non-apify (like mock), route to standard loop
        if data_source.provider_type != "apify_provider":
            cats = db.query(Category).filter(Category.is_active == True).all()
            if category_slug:
                cats = [c for c in cats if c.slug == category_slug.lower()]
            results = []
            for c in cats:
                res = DataSourceService.sync_category(db, c, data_source=data_source, limit=limit)
                results.append(res.model_dump())
            return {
                "status": "success",
                "message": f"Synced {len(results)} categories",
                "results": results
            }

        # 1. Fetch real reels from Apify
        try:
            if hasattr(provider, "fetch_all_reels"):
                raw_reels = provider.fetch_all_reels(limit=limit)
            else:
                raw_reels = provider.fetch_reels_by_category("Niche", limit=limit)
        except Exception as e:
            logger.error(f"Apify fetch error: {e}")
            data_source.status_message = f"Sync error: {str(e)[:180]}"
            data_source.last_synced_at = now
            db.commit()
            raise e

        if not raw_reels:
            data_source.status_message = f"Scraper running in cloud. Tap Sync again in 30 seconds."
            data_source.last_synced_at = now
            db.commit()
            return {
                "status": "pending",
                "message": "Apify scraper run initiated in the cloud. As soon as it finishes scraping, tap 'Sync Real Reels' to import items.",
                "reels_count": 0
            }

        # 2. Real data arrived: purge fake mock data immediately!
        DataSourceService.purge_mock_data(db)

        # 3. Category lookup maps
        all_categories = db.query(Category).all()
        cat_map_by_name = {c.name.lower(): c for c in all_categories}
        cat_map_by_slug = {c.slug.lower(): c for c in all_categories}
        default_cat = cat_map_by_slug.get("niche") or all_categories[0]

        ingested_count = 0
        updated_count = 0
        affected_cat_ids = set()

        # 4. Upsert Creators, Reels, and Metrics
        for idx, item in enumerate(raw_reels):
            try:
                # Target Category
                if category_slug and category_slug.lower() in cat_map_by_slug:
                    target_cat = cat_map_by_slug[category_slug.lower()]
                else:
                    classified_name = classify_reel_category(item.caption)
                    target_cat = cat_map_by_name.get(classified_name.lower())
                    if not target_cat:
                        # Fallback distribution across available categories
                        target_cat = all_categories[idx % len(all_categories)]

                affected_cat_ids.add(target_cat.id)

                # Upsert Creator
                creator = db.query(Creator).filter(Creator.username == item.creator_username).first()
                if not creator:
                    creator = Creator(
                        platform_user_id=item.creator_platform_id,
                        username=item.creator_username,
                        full_name=item.creator_name,
                        profile_pic_url=item.creator_profile_pic,
                        is_verified=item.creator_is_verified,
                        followers_count=item.creator_followers,
                        following_count=item.creator_following,
                        biography=item.creator_bio,
                        profile_url=item.creator_url
                    )
                    db.add(creator)
                    db.flush()
                else:
                    creator.followers_count = item.creator_followers or creator.followers_count
                    creator.full_name = item.creator_name or creator.full_name
                    creator.profile_pic_url = item.creator_profile_pic or creator.profile_pic_url
                    creator.is_verified = item.creator_is_verified
                    db.flush()

                # Upsert Reel
                reel = db.query(Reel).filter(Reel.platform_media_id == item.platform_media_id).first()
                if not reel:
                    reel = Reel(
                        platform_media_id=item.platform_media_id,
                        permalink=item.permalink,
                        caption=item.caption,
                        thumbnail_url=item.thumbnail_url,
                        video_url=item.video_url,
                        duration=item.duration,
                        posted_at=item.posted_at,
                        category_id=target_cat.id,
                        creator_id=creator.id,
                        data_source_id=data_source.id,
                        is_active=True
                    )
                    db.add(reel)
                    db.flush()
                    ingested_count += 1
                else:
                    reel.caption = item.caption or reel.caption
                    reel.thumbnail_url = item.thumbnail_url or reel.thumbnail_url
                    reel.video_url = item.video_url or reel.video_url
                    reel.category_id = target_cat.id
                    db.flush()
                    updated_count += 1

                # Previous metrics
                prev_metrics = (
                    db.query(ReelMetrics)
                    .filter(ReelMetrics.reel_id == reel.id)
                    .order_by(desc(ReelMetrics.recorded_at))
                    .first()
                )

                # New Metrics
                engagement_rate = calculate_engagement_rate(
                    item.view_count, item.like_count, item.comment_count, item.share_count
                )
                metrics = ReelMetrics(
                    reel_id=reel.id,
                    view_count=item.view_count,
                    like_count=item.like_count,
                    comment_count=item.comment_count,
                    share_count=item.share_count,
                    save_count=item.save_count,
                    engagement_rate=engagement_rate,
                    recorded_at=now
                )
                db.add(metrics)
                db.flush()

                # Velocity & Trending Score
                velocity = calculate_growth_velocity(
                    current_metrics=metrics,
                    previous_metrics=prev_metrics,
                    posted_at=reel.posted_at,
                    current_time=now
                )
                score = calculate_composite_popularity_score(
                    views=metrics.view_count,
                    likes=metrics.like_count,
                    comments=metrics.comment_count,
                    shares=metrics.share_count,
                    posted_at=reel.posted_at,
                    current_time=now,
                    velocity=velocity
                )

                trending_record = TrendingScore(
                    reel_id=reel.id,
                    period="24h",
                    score=score,
                    growth_velocity=velocity,
                    recorded_at=now
                )
                db.add(trending_record)

                # Update denormalized cached metrics on Reel
                reel.current_views = metrics.view_count
                reel.current_likes = metrics.like_count
                reel.current_comments = metrics.comment_count
                reel.current_shares = metrics.share_count
                reel.current_saves = metrics.save_count
                reel.current_engagement_rate = engagement_rate
                reel.current_trending_score = score
                reel.current_growth_velocity = velocity

            except Exception as e:
                logger.error(f"Error processing reel {item.platform_media_id}: {e}")

        db.commit()

        # Recalculate ranks for all affected categories
        for cat_id in affected_cat_ids:
            recalculate_category_ranks(db, cat_id)

        data_source.last_synced_at = now
        total_synced = ingested_count + updated_count
        data_source.status_message = f"Successfully synced {total_synced} real reels at {now.strftime('%H:%M:%S UTC')}"
        db.commit()

        return {
            "status": "success",
            "message": f"Successfully ingested {total_synced} real Instagram reels from Apify!",
            "reels_count": total_synced,
            "ingested": ingested_count,
            "updated": updated_count
        }

    @staticmethod
    def sync_category(
        db: Session,
        category: Category,
        data_source: Optional[DataSource] = None,
        limit: int = 50
    ) -> SyncResult:
        """Category-specific sync fallback."""
        if not data_source:
            data_source = db.query(DataSource).filter(DataSource.is_active == True).first()
            if not data_source:
                data_source = DataSourceService.get_or_create_data_source(db)

        config = json.loads(data_source.config_json) if data_source.config_json else {}
        provider = DataSourceService.get_provider(data_source.provider_type, config)
        
        result = SyncResult(
            provider_name=provider.get_provider_name(),
            category_name=category.name
        )
        now = datetime.now(timezone.utc)

        try:
            raw_reels = provider.fetch_reels_by_category(category.name, limit=limit)
        except Exception as e:
            logger.error(f"Error fetching from {provider.get_provider_name()}: {e}")
            result.errors.append(str(e))
            data_source.status_message = f"Sync error: {str(e)[:180]}"
            data_source.last_synced_at = now
            db.commit()
            return result

        if not raw_reels:
            data_source.status_message = f"0 items returned for {category.name}."
            data_source.last_synced_at = now
            db.commit()
            return result

        if data_source.provider_type in ("apify_provider", "official_graph_api"):
            DataSourceService.purge_mock_data(db)

        for item in raw_reels:
            try:
                creator = db.query(Creator).filter(Creator.username == item.creator_username).first()
                if not creator:
                    creator = Creator(
                        platform_user_id=item.creator_platform_id,
                        username=item.creator_username,
                        full_name=item.creator_name,
                        profile_pic_url=item.creator_profile_pic,
                        is_verified=item.creator_is_verified,
                        followers_count=item.creator_followers,
                        following_count=item.creator_following,
                        biography=item.creator_bio,
                        profile_url=item.creator_url
                    )
                    db.add(creator)
                    db.flush()
                else:
                    creator.followers_count = item.creator_followers or creator.followers_count
                    creator.full_name = item.creator_name or creator.full_name
                    creator.profile_pic_url = item.creator_profile_pic or creator.profile_pic_url
                    creator.is_verified = item.creator_is_verified
                    db.flush()

                reel = db.query(Reel).filter(Reel.platform_media_id == item.platform_media_id).first()
                if not reel:
                    reel = Reel(
                        platform_media_id=item.platform_media_id,
                        permalink=item.permalink,
                        caption=item.caption,
                        thumbnail_url=item.thumbnail_url,
                        video_url=item.video_url,
                        duration=item.duration,
                        posted_at=item.posted_at,
                        category_id=category.id,
                        creator_id=creator.id,
                        data_source_id=data_source.id,
                        is_active=True
                    )
                    db.add(reel)
                    db.flush()
                    result.reels_ingested += 1
                else:
                    reel.caption = item.caption or reel.caption
                    reel.thumbnail_url = item.thumbnail_url or reel.thumbnail_url
                    reel.video_url = item.video_url or reel.video_url
                    db.flush()
                    result.reels_updated += 1

                prev_metrics = (
                    db.query(ReelMetrics)
                    .filter(ReelMetrics.reel_id == reel.id)
                    .order_by(desc(ReelMetrics.recorded_at))
                    .first()
                )

                engagement_rate = calculate_engagement_rate(
                    item.view_count, item.like_count, item.comment_count, item.share_count
                )
                metrics = ReelMetrics(
                    reel_id=reel.id,
                    view_count=item.view_count,
                    like_count=item.like_count,
                    comment_count=item.comment_count,
                    share_count=item.share_count,
                    save_count=item.save_count,
                    engagement_rate=engagement_rate,
                    recorded_at=now
                )
                db.add(metrics)
                db.flush()
                result.metrics_recorded += 1

                velocity = calculate_growth_velocity(
                    current_metrics=metrics,
                    previous_metrics=prev_metrics,
                    posted_at=reel.posted_at,
                    current_time=now
                )
                score = calculate_composite_popularity_score(
                    views=metrics.view_count,
                    likes=metrics.like_count,
                    comments=metrics.comment_count,
                    shares=metrics.share_count,
                    posted_at=reel.posted_at,
                    current_time=now,
                    velocity=velocity
                )

                trending_record = TrendingScore(
                    reel_id=reel.id,
                    period="24h",
                    score=score,
                    growth_velocity=velocity,
                    recorded_at=now
                )
                db.add(trending_record)

                reel.current_views = metrics.view_count
                reel.current_likes = metrics.like_count
                reel.current_comments = metrics.comment_count
                reel.current_shares = metrics.share_count
                reel.current_saves = metrics.save_count
                reel.current_engagement_rate = engagement_rate
                reel.current_trending_score = score
                reel.current_growth_velocity = velocity

            except Exception as e:
                logger.error(f"Error processing reel {item.platform_media_id}: {e}")
                result.errors.append(f"Reel {item.platform_media_id}: {str(e)}")

        db.commit()
        recalculate_category_ranks(db, category.id)

        data_source.last_synced_at = now
        data_source.status_message = f"Synced {result.reels_ingested + result.reels_updated} reels at {now.strftime('%H:%M:%S UTC')}"
        db.commit()

        return result

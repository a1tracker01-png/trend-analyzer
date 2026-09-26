import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Type
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
from backend.app.data_sources.apify_provider import ApifyInstagramProvider
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
            logger.warning(f"Provider {provider_type} not found, defaulting to mock_provider")
            provider_cls = MockPermittedProvider
        return provider_cls(config or {})

    @staticmethod
    def get_or_create_data_source(
        db: Session,
        name: str = "Permitted Sandbox Provider",
        provider_type: str = "mock_provider",
        auth_type: str = "none",
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
    def sync_category(
        db: Session,
        category: Category,
        data_source: Optional[DataSource] = None,
        limit: int = 25
    ) -> SyncResult:
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
            logger.error(f"Error fetching data from {provider.get_provider_name()}: {e}")
            result.errors.append(str(e))
            data_source.status_message = f"Sync error: {str(e)[:180]}"
            data_source.last_synced_at = now
            db.commit()
            return result

        if not raw_reels:
            data_source.status_message = f"0 reels returned for {category.name} at {now.strftime('%H:%M:%S UTC')}"
            data_source.last_synced_at = now
            db.commit()
            return result

        for item in raw_reels:
            try:
                # 1. Upsert Creator
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

                # 2. Upsert Reel
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
                    db.flush()
                    result.reels_updated += 1

                # 3. Previous metrics snapshot for velocity
                prev_metrics = (
                    db.query(ReelMetrics)
                    .filter(ReelMetrics.reel_id == reel.id)
                    .order_by(desc(ReelMetrics.recorded_at))
                    .first()
                )

                # 4. Insert New Metrics Snapshot
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

                # 5. Compute Growth Velocity & Composite Popularity Score
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

        rate_info = provider.get_rate_limit_info()
        data_source.last_synced_at = now
        data_source.rate_limit_remaining = rate_info.get("remaining", 200)
        data_source.status_message = f"Synced {result.reels_ingested + result.reels_updated} reels at {now.strftime('%H:%M:%S UTC')}"
        db.commit()

        return result

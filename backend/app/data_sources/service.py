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
        High-velocity batch ingestion.
        Pulls real reels from Apify datasets in < 2s, balances across categories,
        computes trending/growth velocity, and purges all mock data in 1 commit.
        """
        now = datetime.now(timezone.utc)
        config = json.loads(data_source.config_json) if data_source.config_json else {}
        provider = DataSourceService.get_provider(data_source.provider_type, config)

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
            data_source.status_message = "Scraper running in cloud. Tap Sync again in 30 seconds."
            data_source.last_synced_at = now
            db.commit()
            return {
                "status": "pending",
                "message": "Apify scraper run initiated in the cloud. As soon as it finishes scraping, tap 'Sync Real Reels' to import items.",
                "reels_count": 0
            }

        # 2. Real data arrived: purge fake mock data immediately
        DataSourceService.purge_mock_data(db)

        # 3. Lookup caches in memory
        all_categories = db.query(Category).all()
        cat_map_by_name = {c.name.lower(): c for c in all_categories}
        cat_map_by_slug = {c.slug.lower(): c for c in all_categories}
        creators_cache = {c.username: c for c in db.query(Creator).all()}
        reels_cache = {r.platform_media_id: r for r in db.query(Reel).all()}

        # 4. Upsert Creators (Batch 1)
        for item in raw_reels:
            if item.creator_username not in creators_cache:
                c = Creator(
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
                db.add(c)
                creators_cache[item.creator_username] = c
            else:
                existing_c = creators_cache[item.creator_username]
                existing_c.followers_count = item.creator_followers or existing_c.followers_count
                existing_c.full_name = item.creator_name or existing_c.full_name
                existing_c.profile_pic_url = item.creator_profile_pic or existing_c.profile_pic_url

        db.flush()

        # 5. Determine Categories with automatic balancing so no category is empty
        category_assignments = []
        for idx, item in enumerate(raw_reels):
            if category_slug and category_slug.lower() in cat_map_by_slug:
                target_cat = cat_map_by_slug[category_slug.lower()]
            else:
                classified_name = classify_reel_category(item.caption)
                target_cat = cat_map_by_name.get(classified_name.lower())
                if not target_cat:
                    target_cat = all_categories[idx % len(all_categories)]
            category_assignments.append(target_cat)

        # Balance check: ensure all active categories have reels
        cat_counts = {c.id: 0 for c in all_categories}
        for c in category_assignments:
            cat_counts[c.id] += 1

        empty_cats = [c for c in all_categories if cat_counts[c.id] == 0]
        if empty_cats and len(raw_reels) >= len(all_categories):
            # Distribute surplus from the largest categories to fill empty ones
            for empty_cat in empty_cats:
                # Find an index from the most populated category
                max_cat_id = max(cat_counts, key=cat_counts.get)
                if cat_counts[max_cat_id] > 3:
                    for i, assigned_cat in enumerate(category_assignments):
                        if assigned_cat.id == max_cat_id:
                            category_assignments[i] = empty_cat
                            cat_counts[max_cat_id] -= 1
                            cat_counts[empty_cat.id] += 1
                            break

        # 6. Upsert Reels & Precompute Metrics (Batch 2)
        ingested_count = 0
        updated_count = 0

        for idx, item in enumerate(raw_reels):
            creator = creators_cache[item.creator_username]
            target_cat = category_assignments[idx]

            eng = calculate_engagement_rate(item.view_count, item.like_count, item.comment_count, item.share_count)
            vel = round(max(item.view_count / max((now - item.posted_at).total_seconds() / 3600.0, 0.1), 0.0), 2)
            score = calculate_composite_popularity_score(
                item.view_count, item.like_count, item.comment_count, item.share_count, item.posted_at, now, vel
            )

            reel = reels_cache.get(item.platform_media_id)
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
                    is_active=True,
                    current_views=item.view_count,
                    current_likes=item.like_count,
                    current_comments=item.comment_count,
                    current_shares=item.share_count,
                    current_saves=item.save_count,
                    current_engagement_rate=eng,
                    current_trending_score=score,
                    current_growth_velocity=vel
                )
                db.add(reel)
                reels_cache[item.platform_media_id] = reel
                ingested_count += 1
            else:
                reel.caption = item.caption or reel.caption
                reel.thumbnail_url = item.thumbnail_url or reel.thumbnail_url
                reel.video_url = item.video_url or reel.video_url
                reel.category_id = target_cat.id
                reel.current_views = item.view_count
                reel.current_likes = item.like_count
                reel.current_comments = item.comment_count
                reel.current_shares = item.share_count
                reel.current_saves = item.save_count
                reel.current_engagement_rate = eng
                reel.current_trending_score = score
                reel.current_growth_velocity = vel
                updated_count += 1

        db.flush()

        # 7. Add Metrics & TrendingScore snapshots (Batch 3)
        for idx, item in enumerate(raw_reels):
            reel = reels_cache[item.platform_media_id]
            eng = reel.current_engagement_rate
            vel = reel.current_growth_velocity
            score = reel.current_trending_score

            m = ReelMetrics(
                reel_id=reel.id,
                view_count=item.view_count,
                like_count=item.like_count,
                comment_count=item.comment_count,
                share_count=item.share_count,
                save_count=item.save_count,
                engagement_rate=eng,
                recorded_at=now
            )
            db.add(m)

            ts = TrendingScore(
                reel_id=reel.id,
                period="24h",
                score=score,
                growth_velocity=vel,
                recorded_at=now
            )
            db.add(ts)

        # 8. Recalculate Category Ranks in memory
        for cat in all_categories:
            cat_reels = [r for r in reels_cache.values() if r.category_id == cat.id and r.is_active]
            cat_reels.sort(key=lambda r: r.current_trending_score or 0.0, reverse=True)
            for rank, r in enumerate(cat_reels, 1):
                r.current_rank = rank

        # Final single commit
        total_synced = ingested_count + updated_count
        data_source.last_synced_at = now
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

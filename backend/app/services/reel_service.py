from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, or_

from backend.app.models.category import Category
from backend.app.models.creator import Creator
from backend.app.models.reel import Reel
from backend.app.models.reel_metrics import ReelMetrics
from backend.app.models.trending_score import TrendingScore
from backend.app.schemas.reel import ReelResponse, ReelMetricsResponse, TrendingScoreResponse
from backend.app.schemas.creator import CreatorResponse

class ReelService:
    @staticmethod
    def _format_reel_response(reel: Reel) -> ReelResponse:
        creator_resp = None
        if reel.creator:
            creator_resp = CreatorResponse.model_validate(reel.creator)

        metrics_resp = None
        if reel.metrics and len(reel.metrics) > 0:
            metrics_resp = ReelMetricsResponse.model_validate(reel.metrics[0])
        else:
            metrics_resp = ReelMetricsResponse(
                id=0,
                view_count=reel.current_views or 0,
                like_count=reel.current_likes or 0,
                comment_count=reel.current_comments or 0,
                share_count=reel.current_shares or 0,
                save_count=reel.current_saves or 0,
                engagement_rate=reel.current_engagement_rate or 0.0,
                recorded_at=reel.updated_at or reel.created_at
            )

        trending_resp = None
        if reel.trending_scores and len(reel.trending_scores) > 0:
            trending_resp = TrendingScoreResponse.model_validate(reel.trending_scores[0])
        else:
            trending_resp = TrendingScoreResponse(
                id=0,
                period="24h",
                score=reel.current_trending_score or 0.0,
                growth_velocity=reel.current_growth_velocity or 0.0,
                rank=reel.current_rank or 1,
                recorded_at=reel.updated_at or reel.created_at
            )

        return ReelResponse(
            id=reel.id,
            platform_media_id=reel.platform_media_id,
            permalink=reel.permalink,
            caption=reel.caption,
            thumbnail_url=reel.thumbnail_url,
            video_url=reel.video_url,
            duration=reel.duration,
            posted_at=reel.posted_at,
            category_id=reel.category_id,
            category_name=reel.category.name if reel.category else "",
            country=reel.country or (reel.creator.country if reel.creator else None) or "India",
            creator=creator_resp,
            latest_metrics=metrics_resp,
            latest_trending=trending_resp
        )

    @staticmethod
    def get_category_by_slug_or_id(db: Session, identifier: str) -> Optional[Category]:
        if identifier.isdigit():
            return db.query(Category).filter(Category.id == int(identifier)).first()
        return db.query(Category).filter(Category.slug == identifier.lower()).first()

    @staticmethod
    def get_reels(
        db: Session,
        category_id: int,
        filter_mode: str = "all", # "all", "last_24h", "fastest_growing", "top_100"
        sort_by: Optional[str] = None, # "trending", "velocity", "views", "likes", "engagement", "newest"
        country: Optional[str] = None, # "India", "Pakistan", "Bangladesh", "Nepal", "all"
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> Tuple[List[ReelResponse], int]:
        """
        Retrieves reels matching the requested filter mode, sorting, and pagination.
        100% compliant with PostgreSQL and SQLite (no invalid GROUP BY constructs).
        """
        now = datetime.now(timezone.utc)
        
        query = (
            db.query(Reel)
            .join(Category, Reel.category_id == Category.id)
            .outerjoin(Creator, Reel.creator_id == Creator.id)
            .options(
                joinedload(Reel.creator),
                joinedload(Reel.category),
                joinedload(Reel.metrics),
                joinedload(Reel.trending_scores)
            )
            .filter(Reel.category_id == category_id, Reel.is_active == True)
        )

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Reel.caption.ilike(search_term),
                    Creator.username.ilike(search_term),
                    Creator.full_name.ilike(search_term)
                )
            )

        # Apply Country filter - strictly restrict to South Asia regional mix (India, Pakistan, Bangladesh, Nepal)
        south_asia = ["India", "Pakistan", "Bangladesh", "Nepal"]
        if country and country.lower() not in ("all", "", "none"):
            query = query.filter(
                or_(
                    Reel.country.ilike(country),
                    Creator.country.ilike(country)
                )
            )
        else:
            query = query.filter(
                or_(
                    Reel.country.in_(south_asia),
                    Creator.country.in_(south_asia)
                )
            )

        # Apply Filter Mode
        effective_limit = limit
        if filter_mode == "last_24h":
            cutoff_24h = now - timedelta(hours=24)
            query = query.filter(Reel.posted_at >= cutoff_24h)
        elif filter_mode == "fastest_growing":
            sort_by = sort_by or "velocity"
        elif filter_mode == "top_100":
            effective_limit = min(limit, 100) if limit != 50 else 100
            sort_by = sort_by or "trending"

        # Count total records matching filter BEFORE ordering and pagination
        total_count = query.count()

        # Apply Sorting on indexed Reel columns
        sort_by = sort_by or "trending"
        if sort_by == "velocity":
            query = query.order_by(desc(Reel.current_growth_velocity), desc(Reel.posted_at))
        elif sort_by == "views":
            query = query.order_by(desc(Reel.current_views), desc(Reel.posted_at))
        elif sort_by == "likes":
            query = query.order_by(desc(Reel.current_likes), desc(Reel.posted_at))
        elif sort_by == "engagement":
            query = query.order_by(desc(Reel.current_engagement_rate), desc(Reel.posted_at))
        elif sort_by == "newest":
            query = query.order_by(desc(Reel.posted_at))
        elif sort_by == "trending":
            query = query.order_by(desc(Reel.current_trending_score), desc(Reel.posted_at))
        else:
            query = query.order_by(desc(Reel.current_trending_score), desc(Reel.posted_at))

        # Apply pagination
        reels = query.offset(offset).limit(effective_limit).all()

        formatted = [ReelService._format_reel_response(r) for r in reels]
        return formatted, total_count

    @staticmethod
    def get_category_stats(db: Session, category_id: int, country: Optional[str] = None) -> Dict[str, Any]:
        """Calculates dashboard summary metrics for a category without SQL grouping conflicts."""
        now = datetime.now(timezone.utc)
        cutoff_24h = now - timedelta(hours=24)

        base_q = db.query(Reel).join(Creator, Reel.creator_id == Creator.id).filter(
            Reel.category_id == category_id,
            Reel.is_active == True
        )
        south_asia = ["India", "Pakistan", "Bangladesh", "Nepal"]
        if country and country.lower() not in ("all", "", "none"):
            base_q = base_q.filter(
                or_(
                    Reel.country.ilike(country),
                    Creator.country.ilike(country)
                )
            )
        else:
            base_q = base_q.filter(
                or_(
                    Reel.country.in_(south_asia),
                    Creator.country.in_(south_asia)
                )
            )

        total_reels = base_q.count()
        reels_24h = base_q.filter(Reel.posted_at >= cutoff_24h).count()

        metric_aggs = (
            base_q.with_entities(
                func.sum(Reel.current_views),
                func.sum(Reel.current_likes),
                func.avg(Reel.current_engagement_rate)
            ).first()
        )

        total_views = (metric_aggs[0] if metric_aggs else 0) or 0
        total_likes = (metric_aggs[1] if metric_aggs else 0) or 0
        avg_engagement = round((metric_aggs[2] if metric_aggs else 0.0) or 0.0, 2)

        # Fastest growing reel in category
        fastest_reel_row = (
            base_q
            .options(joinedload(Reel.creator), joinedload(Reel.metrics), joinedload(Reel.trending_scores))
            .order_by(desc(Reel.current_growth_velocity))
            .first()
        )
        fastest_growing = ReelService._format_reel_response(fastest_reel_row) if fastest_reel_row else None

        # Top ranked reel in category
        top_reel_row = (
            base_q
            .options(joinedload(Reel.creator), joinedload(Reel.metrics), joinedload(Reel.trending_scores))
            .order_by(desc(Reel.current_trending_score))
            .first()
        )
        top_reel = ReelService._format_reel_response(top_reel_row) if top_reel_row else None

        return {
            "category_id": category_id,
            "total_reels": total_reels,
            "reels_last_24h": reels_24h,
            "total_views": total_views,
            "total_likes": total_likes,
            "avg_engagement_rate": avg_engagement,
            "fastest_growing": fastest_growing,
            "top_reel": top_reel
        }

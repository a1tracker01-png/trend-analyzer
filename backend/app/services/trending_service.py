from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.reel import Reel
from backend.app.models.reel_metrics import ReelMetrics
from backend.app.models.trending_score import TrendingScore

def calculate_engagement_rate(views: int, likes: int, comments: int, shares: int) -> float:
    """
    Standard industry engagement rate calculation based on views:
    Engagement Rate (%) = ((Likes + Comments + Shares) / Views) * 100
    """
    if views <= 0:
        return 0.0
    total_engagements = likes + comments + shares
    rate = (total_engagements / views) * 100.0
    return round(rate, 2)

def calculate_growth_velocity(
    current_metrics: ReelMetrics,
    previous_metrics: Optional[ReelMetrics],
    posted_at: datetime,
    current_time: Optional[datetime] = None
) -> float:
    """
    Calculates growth velocity (views gained per hour).
    If a previous snapshot exists, uses delta views / delta hours.
    Otherwise, uses current views / age in hours.
    """
    now = current_time or datetime.now(timezone.utc)
    
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
        
    if previous_metrics and previous_metrics.recorded_at:
        prev_time = previous_metrics.recorded_at
        if prev_time.tzinfo is None:
            prev_time = prev_time.replace(tzinfo=timezone.utc)
        
        delta_seconds = (now - prev_time).total_seconds()
        delta_hours = max(delta_seconds / 3600.0, 0.05)
        delta_views = max(0, current_metrics.view_count - previous_metrics.view_count)
        velocity = delta_views / delta_hours
    else:
        age_seconds = (now - posted_at).total_seconds()
        age_hours = max(age_seconds / 3600.0, 0.1)
        velocity = current_metrics.view_count / age_hours

    return round(velocity, 2)

def calculate_composite_popularity_score(
    views: int,
    likes: int,
    comments: int,
    shares: int,
    posted_at: datetime,
    current_time: Optional[datetime] = None,
    velocity: float = 0.0
) -> float:
    """
    Calculates a balanced popularity/trending score.
    Higher weight given to active engagements (shares > comments > likes > views).
    Time decay dampens older reels while rewarding fresh content.
    """
    now = current_time or datetime.now(timezone.utc)
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)

    age_hours = max((now - posted_at).total_seconds() / 3600.0, 0.1)
    
    raw_signal = (
        views * 0.2 +
        likes * 1.5 +
        comments * 3.5 +
        shares * 6.0
    )
    
    gravity = 1.15
    decay_factor = (age_hours + 2.0) ** gravity
    
    base_score = raw_signal / decay_factor
    velocity_bonus = min(velocity * 0.05, base_score * 0.4)
    final_score = base_score + velocity_bonus
    
    return round(final_score, 2)

def recalculate_category_ranks(db: Session, category_id: int):
    """
    Ranks all reels within a category by their latest composite trending score.
    Populates current_rank on Reel and rank in TrendingScore.
    """
    reels = (
        db.query(Reel)
        .filter(Reel.category_id == category_id, Reel.is_active == True)
        .order_by(desc(Reel.current_trending_score))
        .all()
    )
    
    rank = 1
    for r in reels:
        r.current_rank = rank
        latest_ts = (
            db.query(TrendingScore)
            .filter(TrendingScore.reel_id == r.id)
            .order_by(desc(TrendingScore.recorded_at))
            .first()
        )
        if latest_ts:
            latest_ts.rank = rank
        rank += 1
            
    db.commit()

import math
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.reel import Reel
from backend.app.models.reel_metrics import ReelMetrics
from backend.app.models.trending_score import TrendingScore

def calculate_engagement_rate(views: int, likes: int, comments: int, shares: int) -> float:
    """
    Calculates engagement rate percentage: ((likes + comments*2 + shares*3) / views) * 100
    Higher weights are given to comments and shares as stronger signals of virality.
    """
    if views <= 0:
        return 0.0
    weighted_interactions = likes + (comments * 2.0) + (shares * 3.0)
    rate = (weighted_interactions / views) * 100.0
    return round(min(rate, 100.0), 2)

def calculate_growth_velocity(
    current_metrics: ReelMetrics,
    previous_metrics: Optional[ReelMetrics],
    posted_at: datetime,
    current_time: Optional[datetime] = None
) -> float:
    """
    Calculates hourly view velocity.
    If previous snapshot exists: (delta_views / delta_hours).
    Otherwise: (current_views / hours_since_post).
    """
    if not current_time:
        current_time = datetime.now(timezone.utc)

    if previous_metrics and previous_metrics.recorded_at:
        delta_seconds = (current_metrics.recorded_at - previous_metrics.recorded_at).total_seconds()
        delta_hours = max(delta_seconds / 3600.0, 0.05)  # min 3 minutes threshold
        delta_views = max(current_metrics.view_count - previous_metrics.view_count, 0)
        velocity = delta_views / delta_hours
    else:
        age_seconds = (current_time - posted_at).total_seconds()
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
    HackerNews-style exponential decay gravity algorithm tailored for short-form video:
    Score = (W_views*V + W_likes*L + W_comments*C + W_shares*S) / (Age_hours + 2)^gravity + Velocity_Bonus
    """
    if not current_time:
        current_time = datetime.now(timezone.utc)

    w_views = 0.05
    w_likes = 1.0
    w_comments = 2.5
    w_shares = 4.0

    raw_signal = (views * w_views) + (likes * w_likes) + (comments * w_comments) + (shares * w_shares)
    age_seconds = max((current_time - posted_at).total_seconds(), 0)
    age_hours = age_seconds / 3600.0

    gravity = 1.15
    decay_factor = (age_hours + 2.0) ** gravity
    
    base_score = raw_signal / decay_factor
    velocity_bonus = min(velocity * 0.05, base_score * 0.4)
    final_score = base_score + velocity_bonus
    
    return round(final_score, 2)

def recalculate_category_ranks(db: Session, category_id: int):
    """
    Ranks all reels within a category by their latest composite trending score.
    Fast in-memory ranking with zero N+1 database queries.
    """
    reels = (
        db.query(Reel)
        .filter(Reel.category_id == category_id, Reel.is_active == True)
        .order_by(desc(Reel.current_trending_score))
        .all()
    )
    for rank, r in enumerate(reels, 1):
        r.current_rank = rank

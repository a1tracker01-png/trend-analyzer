from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.reel import Reel
from backend.app.models.reel_metrics import ReelMetrics
from backend.app.models.trending_score import TrendingScore

def calculate_engagement_rate(views: int, likes: int, comments: int, shares: int) -> float:
    """
    Standard industry engagement rate calculation based on views:
    Engagement Rate (%) = ((Likes + Comments + Shares) / Views) * 100
    Returns percentage float rounded to 2 decimal places.
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
    
    # Ensure posted_at is timezone aware
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
        
    if previous_metrics and previous_metrics.recorded_at:
        prev_time = previous_metrics.recorded_at
        if prev_time.tzinfo is None:
            prev_time = prev_time.replace(tzinfo=timezone.utc)
        
        delta_seconds = (now - prev_time).total_seconds()
        delta_hours = max(delta_seconds / 3600.0, 0.05) # Minimum 3 minutes to avoid zero div
        delta_views = max(0, current_metrics.view_count - previous_metrics.view_count)
        velocity = delta_views / delta_hours
    else:
        age_seconds = (now - posted_at).total_seconds()
        age_hours = max(age_seconds / 3600.0, 0.1) # Minimum 6 minutes
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
    Velocity bonus rewards reels rapidly surging in the last few hours.
    """
    now = current_time or datetime.now(timezone.utc)
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)

    age_hours = max((now - posted_at).total_seconds() / 3600.0, 0.1)
    
    # Engagement weights
    raw_signal = (
        views * 0.2 +
        likes * 1.5 +
        comments * 3.5 +
        shares * 6.0
    )
    
    # HackerNews / Reddit gravity decay formula: Signal / (Age + 2)^gravity
    gravity = 1.15
    decay_factor = (age_hours + 2.0) ** gravity
    
    base_score = raw_signal / decay_factor
    
    # Add a velocity bonus factor (up to 30% boost for surging growth)
    velocity_bonus = min(velocity * 0.05, base_score * 0.4)
    final_score = base_score + velocity_bonus
    
    return round(final_score, 2)

def recalculate_category_ranks(db: Session, category_id: int):
    """
    Ranks all reels within a category by their latest composite trending score.
    Populates the 'rank' column in TrendingScore (1 = #1 Top Trending).
    """
    # Fetch latest trending score for each reel in category
    subquery = (
        db.query(TrendingScore.reel_id, TrendingScore.score)
        .join(Reel, Reel.id == TrendingScore.reel_id)
        .filter(Reel.category_id == category_id, Reel.is_active == True)
        .order_by(desc(TrendingScore.score))
        .all()
    )
    
    rank = 1
    for row in subquery:
        reel_id = row[0]
        # Update latest trending score record for this reel
        latest_ts = (
            db.query(TrendingScore)
            .filter(TrendingScore.reel_id == reel_id)
            .order_by(desc(TrendingScore.recorded_at))
            .first()
        )
        if latest_ts:
            latest_ts.rank = rank
            rank += 1
            
    db.commit()

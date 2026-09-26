from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models.reel import Reel
from backend.app.models.reel_metrics import ReelMetrics
from backend.app.schemas.reel import ReelListResponse, ReelResponse, ReelMetricsResponse
from backend.app.services.reel_service import ReelService

router = APIRouter(prefix="/api/reels", tags=["Reels"])

@router.get("", response_model=ReelListResponse)
def get_reels(
    category: str = Query(..., description="Category slug ('niche', 'ai', 'other') or ID"),
    filter_mode: str = Query("all", description="Filter mode: 'all', 'last_24h', 'fastest_growing', 'top_100'"),
    sort_by: Optional[str] = Query(None, description="Sort by: 'trending', 'velocity', 'views', 'likes', 'engagement', 'newest'"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search term for caption or creator"),
    db: Session = Depends(get_db)
):
    """
    Returns reels matching the category, filter, and sort criteria.
    Supports:
      - Last 24 Hours: strictly reels posted within the last 24 hours
      - Fastest Growing: ordered by growth velocity
      - Top 100: top 100 ranked by popularity score
      - Popularity sorting
    """
    cat = ReelService.get_category_by_slug_or_id(db, category)
    if not cat:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    items, total_count = ReelService.get_reels(
        db=db,
        category_id=cat.id,
        filter_mode=filter_mode,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        search=search
    )

    return ReelListResponse(
        category_id=cat.id,
        category_name=cat.name,
        filter_applied=filter_mode,
        total_count=total_count,
        items=items
    )

@router.get("/{reel_id}", response_model=ReelResponse)
def get_reel_by_id(reel_id: int, db: Session = Depends(get_db)):
    """Fetches details for a single reel."""
    reel = db.query(Reel).filter(Reel.id == reel_id).first()
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")
    return ReelService._format_reel_response(reel)

@router.get("/{reel_id}/metrics-history", response_model=List[ReelMetricsResponse])
def get_reel_metrics_history(reel_id: int, db: Session = Depends(get_db)):
    """Returns historical metric snapshots for a reel to visualize growth."""
    reel = db.query(Reel).filter(Reel.id == reel_id).first()
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")

    metrics = (
        db.query(ReelMetrics)
        .filter(ReelMetrics.reel_id == reel_id)
        .order_by(desc(ReelMetrics.recorded_at))
        .limit(20)
        .all()
    )
    return [ReelMetricsResponse.model_validate(m) for m in metrics]

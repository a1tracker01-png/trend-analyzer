import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.competitor import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    CompetitorReelItem,
    SpikeAlertItem,
    CompetitorStatsOverview,
)
from backend.app.services.competitor_service import CompetitorService, KNOWN_CREATOR_PROFILES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/competitors", tags=["Competitor Analytics & Alerts"])

@router.get("", response_model=List[CompetitorResponse])
def get_competitors(db: Session = Depends(get_db)):
    """List all tracked competitors with live analytics and spike metrics."""
    return CompetitorService.get_all_competitors(db)

@router.post("", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
def add_competitor(payload: CompetitorCreate, db: Session = Depends(get_db)):
    """Manually add a specific creator/competitor to tracking."""
    try:
        return CompetitorService.add_competitor(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding competitor: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add competitor: {str(e)}")

@router.delete("/{competitor_id}")
def remove_competitor(competitor_id: int, db: Session = Depends(get_db)):
    """Manually remove a creator/competitor from tracking."""
    success = CompetitorService.remove_competitor(db, competitor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"status": "success", "message": "Competitor removed successfully", "id": competitor_id}

@router.post("/scrape")
def scrape_all_competitors(db: Session = Depends(get_db)):
    """Scrape real-time reel/content data exclusively for all added competitors."""
    try:
        return CompetitorService.scrape_all_competitors(db)
    except Exception as e:
        logger.error(f"Error scraping competitor data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape competitors: {str(e)}")

@router.post("/{competitor_id}/scrape")
def scrape_single_competitor(competitor_id: int, db: Session = Depends(get_db)):
    """Scrape real-time reel/content data for a specific added competitor."""
    from backend.app.models.competitor import Competitor
    comp = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    count = CompetitorService.scrape_single_competitor(db, comp)
    return {
        "status": "success",
        "username": comp.username,
        "reels_ingested": count,
        "message": f"Successfully synced real-time reels for @{comp.username}"
    }

@router.get("/reels", response_model=List[CompetitorReelItem])
def get_competitor_reels(
    timeframe: str = Query("all", description="Timeframe: '24h', '2d', '7d', 'all'"),
    min_views: int = Query(0, description="Minimum view threshold (e.g. 500000, 1000000)"),
    competitor: Optional[str] = Query(None, description="Filter by creator username or 'all'"),
    sort_by: str = Query("views", description="'views', 'growth_velocity', 'recent', 'engagement'"),
    limit: int = Query(50, ge=1, le=150),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get scraped Reels exclusively for added competitors.
    Filter by standard timeframes (past 24h, 2d, 1w) and view thresholds (500k+, 1M+ views).
    """
    return CompetitorService.get_filtered_competitor_reels(
        db=db,
        timeframe=timeframe,
        min_views=min_views,
        competitor_username=competitor,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )

@router.get("/alerts", response_model=List[SpikeAlertItem])
def get_spike_alerts(
    min_velocity: float = Query(20000.0, description="Minimum views/hour surge velocity"),
    db: Session = Depends(get_db)
):
    """
    Spike Alert Section:
    Highlight Reels from the added competitors that are currently
    experiencing a rapid surge/spike in views in real time.
    """
    return CompetitorService.get_spike_alerts(db=db, min_velocity=min_velocity)

@router.get("/stats", response_model=CompetitorStatsOverview)
def get_competitor_stats(db: Session = Depends(get_db)):
    """Aggregate statistics for competitor tracking."""
    return CompetitorService.get_stats_overview(db)

@router.get("/suggestions")
def get_suggested_competitors():
    """List recommended tech creators that users can quickly add as competitors."""
    suggestions = []
    for username, info in KNOWN_CREATOR_PROFILES.items():
        suggestions.append({
            "username": username,
            "name": info.get("name"),
            "category": info.get("category", "Tech"),
            "avatar": info.get("avatar"),
            "followers": info.get("followers", 0),
            "bio": info.get("bio")
        })
    return suggestions

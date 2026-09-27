from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.category import Category
from backend.app.models.reel import Reel
from backend.app.schemas.category import CategoryResponse
from backend.app.services.reel_service import ReelService

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponse])
def get_categories(country: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Returns the list of content categories with counts."""
    categories = db.query(Category).filter(Category.is_active == True).order_by(Category.id).all()
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)

    results = []
    south_asia = ["India", "Pakistan", "Bangladesh", "Nepal"]
    for cat in categories:
        q = db.query(Reel).filter(Reel.category_id == cat.id, Reel.is_active == True)
        if country and country.lower() not in ("all", "", "none"):
            q = q.filter(Reel.country.ilike(country))
        else:
            q = q.filter(Reel.country.in_(south_asia))
        total = q.count()
        last_24h = q.filter(Reel.posted_at >= cutoff_24h).count()

        results.append(
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                description=cat.description,
                icon=cat.icon,
                color=cat.color,
                is_active=cat.is_active,
                total_reels=total,
                reels_last_24h=last_24h
            )
        )
    return results

@router.get("/{slug_or_id}")
def get_category_details(
    slug_or_id: str, 
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns detailed stats for a category."""
    cat = ReelService.get_category_by_slug_or_id(db, slug_or_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    stats = ReelService.get_category_stats(db, cat.id, country=country)
    return {
        "category": {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "icon": cat.icon,
            "color": cat.color
        },
        "stats": stats
    }

@router.get("/{slug_or_id}/stats")
def get_category_stats_alias(
    slug_or_id: str, 
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return get_category_details(slug_or_id, country=country, db=db)

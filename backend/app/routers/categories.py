from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.category import Category
from backend.app.models.reel import Reel
from backend.app.schemas.category import CategoryResponse
from backend.app.services.reel_service import ReelService

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Returns the list of content categories with counts."""
    categories = db.query(Category).filter(Category.is_active == True).order_by(Category.id).all()
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)

    results = []
    for cat in categories:
        total = db.query(func.count(Reel.id)).filter(Reel.category_id == cat.id, Reel.is_active == True).scalar() or 0
        last_24h = (
            db.query(func.count(Reel.id))
            .filter(Reel.category_id == cat.id, Reel.posted_at >= cutoff_24h, Reel.is_active == True)
            .scalar() or 0
        )
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
def get_category_details(slug_or_id: str, db: Session = Depends(get_db)):
    """Returns detailed stats for a category."""
    cat = ReelService.get_category_by_slug_or_id(db, slug_or_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    stats = ReelService.get_category_stats(db, cat.id)
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
def get_category_stats_alias(slug_or_id: str, db: Session = Depends(get_db)):
    return get_category_details(slug_or_id, db)

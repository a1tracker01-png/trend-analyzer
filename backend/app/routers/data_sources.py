import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.category import Category
from backend.app.models.data_source import DataSource
from backend.app.schemas.data_source import (
    DataSourceResponse,
    DataSourceUpdate,
    DataSourceHealthResponse
)
from backend.app.data_sources.service import DataSourceService

router = APIRouter(prefix="/api/data-sources", tags=["Data Sources"])

@router.get("", response_model=List[DataSourceResponse])
def list_data_sources(db: Session = Depends(get_db)):
    """Lists all configured data source providers."""
    sources = db.query(DataSource).order_by(DataSource.id).all()
    return sources

@router.get("/active", response_model=DataSourceResponse)
def get_active_data_source(db: Session = Depends(get_db)):
    """Returns the currently active data source."""
    source = db.query(DataSource).filter(DataSource.is_active == True).first()
    if not source:
        source = DataSourceService.get_or_create_data_source(db)
    return source

@router.get("/health", response_model=DataSourceHealthResponse)
def check_active_data_source_health(db: Session = Depends(get_db)):
    """Checks health and connection status of the active data source."""
    source = db.query(DataSource).filter(DataSource.is_active == True).first()
    if not source:
        source = DataSourceService.get_or_create_data_source(db)

    config = json.loads(source.config_json) if source.config_json else {}
    provider = DataSourceService.get_provider(source.provider_type, config)
    health = provider.check_health()
    rate_info = provider.get_rate_limit_info()

    return DataSourceHealthResponse(
        provider_name=provider.get_provider_name(),
        provider_type=source.provider_type,
        healthy=health.get("healthy", False),
        status=health.get("status", "unknown"),
        message=health.get("message"),
        configured=health.get("configured", False),
        rate_limit=rate_info
    )

@router.post("/{source_id}/activate", response_model=DataSourceResponse)
def activate_data_source(source_id: int, db: Session = Depends(get_db)):
    """Sets the designated data source as active."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    db.query(DataSource).update({DataSource.is_active: False})
    source.is_active = True
    db.commit()
    db.refresh(source)
    return source

@router.put("/{source_id}", response_model=DataSourceResponse)
def update_data_source_config(source_id: int, payload: DataSourceUpdate, db: Session = Depends(get_db)):
    """Updates settings or credentials for a data source provider."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    current_config = json.loads(source.config_json) if source.config_json else {}
    if payload.access_token is not None:
        current_config["access_token"] = payload.access_token
    if payload.account_id is not None:
        current_config["account_id"] = payload.account_id
    if payload.api_token is not None:
        current_config["api_token"] = payload.api_token
    if payload.actor_id is not None:
        current_config["actor_id"] = payload.actor_id

    source.config_json = json.dumps(current_config)
    if payload.provider_type:
        source.provider_type = payload.provider_type
    if payload.api_endpoint:
        source.api_endpoint = payload.api_endpoint
    if payload.is_active is not None:
        source.is_active = payload.is_active

    db.commit()
    db.refresh(source)
    return source

@router.post("/{source_id}/sync")
def trigger_data_source_sync(
    source_id: int,
    category_slug: Optional[str] = Query(None, description="Optional category to sync specifically"),
    db: Session = Depends(get_db)
):
    """Triggers compliant data ingestion from the selected provider."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    results = []
    if category_slug:
        cat = db.query(Category).filter(Category.slug == category_slug.lower()).first()
        if not cat:
            raise HTTPException(status_code=404, detail=f"Category '{category_slug}' not found")
        categories = [cat]
    else:
        categories = db.query(Category).filter(Category.is_active == True).all()

    for cat in categories:
        res = DataSourceService.sync_category(db, cat, data_source=source)
        results.append(res.model_dump())

    return {
        "status": "success",
        "data_source": source.name,
        "results": results
    }

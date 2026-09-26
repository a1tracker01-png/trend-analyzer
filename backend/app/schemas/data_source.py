from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class DataSourceResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    api_endpoint: Optional[str] = None
    auth_type: str
    is_active: bool
    rate_limit_limit: int
    rate_limit_remaining: int
    rate_limit_reset_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    status_message: Optional[str] = None

    class Config:
        from_attributes = True

class DataSourceUpdate(BaseModel):
    provider_type: Optional[str] = None
    api_endpoint: Optional[str] = None
    access_token: Optional[str] = None
    account_id: Optional[str] = None
    api_token: Optional[str] = None
    actor_id: Optional[str] = None
    is_active: Optional[bool] = None

class DataSourceHealthResponse(BaseModel):
    provider_name: str
    provider_type: str
    healthy: bool
    status: str
    message: Optional[str] = None
    configured: bool
    rate_limit: Dict[str, Any]

class SyncRequest(BaseModel):
    api_token: Optional[str] = None
    category_slug: Optional[str] = None

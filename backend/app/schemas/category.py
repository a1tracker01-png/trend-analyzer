from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = "sparkles"
    color: Optional[str] = "#8B5CF6"
    is_active: bool = True
    total_reels: int = 0
    reels_last_24h: int = 0

    class Config:
        from_attributes = True

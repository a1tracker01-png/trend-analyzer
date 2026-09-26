from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CreatorResponse(BaseModel):
    id: int
    platform_user_id: Optional[str] = None
    username: str
    full_name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    is_verified: bool = False
    followers_count: int = 0
    following_count: int = 0
    biography: Optional[str] = None
    profile_url: Optional[str] = None

    class Config:
        from_attributes = True

"""Group schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    is_active: bool
    created_at: Optional[datetime] = None
    member_count: int = 0

    class Config:
        from_attributes = True


class GroupMemberAdd(BaseModel):
    user_ids: List[int]


class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: Optional[str] = None
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True

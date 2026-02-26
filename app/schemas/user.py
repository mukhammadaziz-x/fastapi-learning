from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Shared base
class UserBase(BaseModel):
    email: EmailStr
    username: str


# For creation requests — includes password
class UserCreate(UserBase):
    password: str


# For partial update requests — all fields optional
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


# For API responses — never exposes password
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True   # Pydantic v2 (was orm_mode in v1)
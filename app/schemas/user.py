from pydantic import BaseModel, EmailStr
from datetime import datetime

# Shared base
class UserBase(BaseModel):
    email: EmailStr
    username: str

# For creation requests — includes password
class UserCreate(UserBase):
    password: str

# For API responses — never exposes password
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True   # Pydantic v2 (was orm_mode in v1)
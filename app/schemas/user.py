"""User schemas."""
import re
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ========== AUTH ==========
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(
        min_length=8,
        description="Kamida 8 ta belgi, 1 ta katta harf, 1 ta kichik harf, 1 ta raqam va 1 ta maxsus belgi bo'lishi kerak.",
    )
    full_name: Optional[str] = None
    # Public registration har doim student sifatida yaratiladi
    role: str = Field(default="student", pattern="^(student)$")
    student_id_number: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        pattern = r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$ %^&*-]).{8,}$"
        if not re.fullmatch(pattern, v):
            raise ValueError(
                "Parol kamida 8 ta belgi, 1 ta katta harf, 1 ta kichik harf, 1 ta raqam va 1 ta maxsus belgi bo'lishi kerak."
            )
        return v


class LoginRequest(BaseModel):
    username: str  # can be username or email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class GoogleAuthCallback(BaseModel):
    code: str
    role: str = "student"


# ========== USER CRUD ==========
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str = "student"


class UserCreate(UserBase):
    password: str
    student_id_number: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    student_id_number: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    auth_provider: str = "local"
    student_id_number: Optional[str] = None
    total_score: float = 0
    ranking_points: float = 0
    streak_days: int = 0
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPublicProfile(BaseModel):
    """Public profile for leaderboard - no sensitive data."""
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    total_score: float = 0
    ranking_points: float = 0
    streak_days: int = 0

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(
        min_length=8,
        description="Kamida 8 ta belgi, 1 ta katta harf, 1 ta kichik harf, 1 ta raqam va 1 ta maxsus belgi bo'lishi kerak.",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        pattern = r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$ %^&*-]).{8,}$"
        if not re.fullmatch(pattern, v):
            raise ValueError(
                "Parol kamida 8 ta belgi, 1 ta katta harf, 1 ta kichik harf, 1 ta raqam va 1 ta maxsus belgi bo'lishi kerak."
            )
        return v

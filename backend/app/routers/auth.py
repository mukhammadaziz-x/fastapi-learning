from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Student, Teacher, UserRole
from app.auth import (
    validate_email, validate_password,
    hash_password, verify_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


ROLE_REDIRECTS = {
    "admin": "/pdp-education-admin/dashboard.html",
    "teacher": "/pages/teacher/dashboard.html",
    "student": "/pages/student/dashboard.html",
}


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Student self-registration only."""
    if not validate_email(body.email):
        raise HTTPException(status_code=422, detail="Invalid email format")
    if not validate_password(body.password):
        raise HTTPException(
            status_code=422,
            detail=(
                "Password must be at least 8 characters and include "
                "uppercase, lowercase, digit, and special character (#?!@$ %^&*-)."
            ),
        )

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=UserRole.student,
    )
    db.add(user)
    await db.flush()

    student = Student(user_id=user.id)
    db.add(student)
    await db.commit()
    await db.refresh(user)

    return {"message": "Registered successfully", "user_id": user.id}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})

    return TokenResponse(
        access_token=token,
        role=user.role.value,
        full_name=user.full_name,
        user_id=user.id,
    )

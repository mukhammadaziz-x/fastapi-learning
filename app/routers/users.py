"""User management router (Admin + self)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.crud import user as user_crud
from app.schemas.user import UserResponse, UserUpdate, UserPublicProfile
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """List users (admin sees all, teacher sees students)."""
    if current_user.role == "teacher":
        role = "student"
    return user_crud.get_users(db, skip=skip, limit=limit, role=role)


@router.get("/search", response_model=list[UserPublicProfile])
def search_users(
    q: str = Query(..., min_length=1),
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Search users by name, email, or username."""
    return user_crud.search_users(db, q, role=role)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get user by ID."""
    user = user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role == "student" and current_user.id != user_id:
        return UserPublicProfile.model_validate(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update user. Users can update themselves; admins can update anyone."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    user = user_crud.update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Delete user (admin only)."""
    if not user_crud.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return None

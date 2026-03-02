"""User CRUD operations."""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.security import hash_password, verify_password


def create_user_from_register(db: Session, email: str, username: str, password: str,
                              full_name: str = None, role: str = "student",
                              student_id_number: str = None) -> User:
    """Create a new user (registration)."""
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        hashed_pwd=hash_password(password),
        role=role,
        auth_provider="local",
        student_id_number=student_id_number,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_google_user(db: Session, email: str, full_name: str, google_id: str,
                       avatar_url: str = None, role: str = "student") -> User:
    """Create user from Google OAuth."""
    username = email.split("@")[0]
    existing = get_user_by_username(db, username)
    counter = 1
    base_username = username
    while existing:
        username = f"{base_username}{counter}"
        existing = get_user_by_username(db, username)
        counter += 1

    user = User(
        email=email,
        username=username,
        full_name=full_name,
        google_id=google_id,
        avatar_url=avatar_url,
        role=role,
        auth_provider="google",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, login: str, password: str) -> Optional[User]:
    """Authenticate by username or email."""
    user = db.query(User).filter(
        or_(User.username == login, User.email == login)
    ).first()
    if not user or not user.hashed_pwd:
        return None
    if not verify_password(password, user.hashed_pwd):
        return None
    return user


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    return db.query(User).filter(User.google_id == google_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100,
              role: str = None, is_active: bool = None) -> list[User]:
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    return q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()


def get_users_count(db: Session, role: str = None) -> int:
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    return q.count()


def update_user(db: Session, user_id: int, data: UserUpdate) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_pwd"] = hash_password(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def search_users(db: Session, query: str, role: str = None, limit: int = 20) -> list[User]:
    q = db.query(User).filter(
        or_(
            User.username.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%"),
            User.full_name.ilike(f"%{query}%"),
        )
    )
    if role:
        q = q.filter(User.role == role)
    return q.limit(limit).all()

# app/crud/user.py
import bcrypt
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Create ──────────────────────────────────────────────
def create_user(db: Session, user: UserCreate) -> User:
    hashed = hash_password(user.password)   # Never store plaintext
    db_user = User(
        email      = user.email,
        username   = user.username,
        hashed_pwd = hashed,
    )
    db.add(db_user)      # Stage the INSERT
    db.commit()          # Flush + persist transaction
    db.refresh(db_user)  # Reload from DB (gets auto id, created_at…)
    return db_user


# ── Read ────────────────────────────────────────────────
def get_user(db: Session, user_id: int) -> User | None:
    """Fetch single user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch user by email (unique)."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    """Fetch user by username (unique)."""
    return db.query(User).filter(User.username == username).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """Paginated list of active users."""
    return (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Update ──────────────────────────────────────────────
def update_user(db: Session, user_id: int, payload: UserUpdate) -> User | None:
    """Update user fields. Hash password if provided."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    update_data = payload.model_dump(exclude_unset=True)  # Only changed fields

    # Hash password before storing
    if "password" in update_data:
        update_data["hashed_pwd"] = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


# ── Delete ──────────────────────────────────────────────
def delete_user(db: Session, user_id: int) -> bool:
    """Hard delete user. Returns True if deleted, False if not found."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

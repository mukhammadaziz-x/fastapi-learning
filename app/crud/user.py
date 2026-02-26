# app/crud/user.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db: Session, user: UserCreate) -> User:
    hashed = pwd_context.hash(user.password)   # Never store plaintext
    db_user = User(
        email      = user.email,
        username   = user.username,
        hashed_pwd = hashed,
    )
    db.add(db_user)      # Stage the INSERT
    db.commit()          # Flush + persist transaction
    db.refresh(db_user)  # Reload from DB (gets auto id, created_at…)
    return db_user

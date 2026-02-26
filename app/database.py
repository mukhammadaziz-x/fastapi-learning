# app/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:1111111@localhost:5432/fastapi"
)

# echo=True logs all SQL — disable in production
engine = create_engine(DATABASE_URL, echo=False)

# autocommit=False: we manage transactions explicitly
# autoflush=False : prevents premature DB flushes
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False
)

Base = declarative_base()


def get_db() -> Generator:
    """Yield a DB session; always close after request."""
    db = SessionLocal()
    try:
        yield db          # handed to the route handler
    finally:
        db.close()        # runs even if an exception is raised

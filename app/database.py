# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://postgres:1111111@localhost:5432/fastapi")

# echo=True logs all SQL — disable in production
engine = create_engine(DATABASE_URL, echo=False)

# autocommit=False: we manage transactions explicitly
# autoflush=False : prevents premature DB flushes
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False
)

Base = declarative_base()
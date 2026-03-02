"""Application configuration settings."""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()


class Settings(BaseSettings):
    # App
    APP_NAME: str = "EduPlatform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-!@#$%")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:1111111@localhost:5432/fastapi"
    )

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-me")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")

    # Grading thresholds
    PASS_THRESHOLD: float = 60.0
    MERIT_THRESHOLD: float = 61.0
    DISTINCTION_THRESHOLD: float = 90.0

    # Ranking
    RANKING_WEIGHTS: dict = {
        "score": 0.4,
        "feedback_positive": 0.2,
        "feedback_negative": -0.1,
        "consistency": 0.15,
        "speed": 0.1,
        "streak": 0.15,
    }

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

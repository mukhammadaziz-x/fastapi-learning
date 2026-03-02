"""Leaderboard cache model - precomputed rankings."""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, func
from app.database import Base


class LeaderboardCache(Base):
    """Cached leaderboard data for fast retrieval."""
    __tablename__ = "leaderboard_cache"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Scope
    scope = Column(String(50), nullable=False, default="global")
    # global, subject_{id}, group_{id}
    scope_id = Column(Integer, nullable=True)  # subject_id or group_id

    # Rankings
    rank = Column(Integer, nullable=False)
    total_score = Column(Float, default=0)
    average_percentage = Column(Float, default=0)
    assignments_completed = Column(Integer, default=0)
    ranking_points = Column(Float, default=0)

    # Streak
    current_streak = Column(Integer, default=0)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())

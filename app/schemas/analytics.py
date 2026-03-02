"""Analytics & Leaderboard schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ========== LEADERBOARD ==========
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_score: float = 0
    average_percentage: float = 0
    assignments_completed: int = 0
    ranking_points: float = 0
    current_streak: int = 0

    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    scope: str  # global, subject, group
    scope_id: Optional[int] = None
    total_participants: int = 0
    entries: List[LeaderboardEntry] = []
    my_rank: Optional[int] = None
    updated_at: Optional[datetime] = None


# ========== ANALYTICS ==========
class StudentAnalytics(BaseModel):
    user_id: int
    username: str
    total_assignments: int = 0
    completed_assignments: int = 0
    average_score: float = 0
    average_percentage: float = 0
    total_time_spent_minutes: float = 0
    grade_distribution: dict = {}  # {"PASS": 5, "MERIT": 3, "DISTINCTION": 2}
    subject_scores: List[dict] = []  # [{"subject": "Math", "avg_score": 85}]
    weekly_activity: List[dict] = []  # [{"week": "2025-W01", "submissions": 3}]
    streak_days: int = 0
    ranking_points: float = 0
    global_rank: Optional[int] = None
    feedbacks_summary: dict = {}  # {"positive": 10, "negative": 2, "neutral": 5}


class SubjectAnalytics(BaseModel):
    subject_id: int
    subject_name: str
    total_students: int = 0
    total_assignments: int = 0
    average_score: float = 0
    completion_rate: float = 0
    grade_distribution: dict = {}
    top_students: List[LeaderboardEntry] = []
    assignment_stats: List[dict] = []


class TeacherDashboard(BaseModel):
    teacher_id: int
    total_subjects: int = 0
    total_students: int = 0
    total_assignments: int = 0
    pending_reviews: int = 0  # submissions needing manual grading
    recent_submissions: List[dict] = []
    subject_overview: List[dict] = []
    ai_flagged_count: int = 0


class AdminDashboard(BaseModel):
    total_users: int = 0
    total_teachers: int = 0
    total_students: int = 0
    total_subjects: int = 0
    total_assignments: int = 0
    total_submissions: int = 0
    active_assignments: int = 0
    platform_average_score: float = 0
    recent_registrations: List[dict] = []
    top_subjects: List[dict] = []

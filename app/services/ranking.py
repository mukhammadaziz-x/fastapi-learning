"""
Ranking Algorithm Service

This implements a comprehensive ranking system:
- Score-based ranking (40%)
- Positive feedback bonus (20%)
- Negative feedback penalty (-10%)
- Consistency score (15%) - how consistently student performs
- Speed bonus (10%) - completing assignments faster
- Streak bonus (15%) - consecutive days of activity
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.user import User
from app.models.submission import Submission
from app.models.enrollment import Enrollment
from app.models.feedback import Feedback
from app.models.leaderboard import LeaderboardCache
from app.models.assignment import Assignment
from app.core.config import settings


def calculate_student_ranking_points(db: Session, student_id: int) -> float:
    """
    Calculate comprehensive ranking points for a student.

    Formula:
    ranking_points = (score_component * 0.4) + (feedback_component * 0.2) +
                     (consistency_component * 0.15) + (speed_component * 0.1) +
                     (streak_component * 0.15) - (negative_feedback_penalty * 0.1)
    """
    weights = settings.RANKING_WEIGHTS

    # 1. Score component: average percentage across all graded submissions
    score_data = db.query(
        func.avg(Submission.percentage),
        func.count(Submission.id)
    ).filter(
        and_(Submission.student_id == student_id,
             Submission.status.in_(["graded", "submitted"]))
    ).first()
    avg_percentage = score_data[0] or 0
    total_submissions = score_data[1] or 0
    score_component = avg_percentage * weights["score"]

    # 2. Positive feedback component
    positive_feedbacks = db.query(func.count(Feedback.id)).filter(
        and_(Feedback.student_id == student_id, Feedback.feedback_type == "positive")
    ).scalar() or 0
    positive_impact = db.query(func.sum(Feedback.ranking_impact)).filter(
        and_(Feedback.student_id == student_id, Feedback.feedback_type == "positive")
    ).scalar() or 0
    feedback_component = (positive_feedbacks * 2 + positive_impact) * weights["feedback_positive"]

    # 3. Negative feedback penalty
    negative_impact = db.query(func.sum(Feedback.ranking_impact)).filter(
        and_(Feedback.student_id == student_id, Feedback.feedback_type == "negative")
    ).scalar() or 0
    negative_component = abs(negative_impact) * weights["feedback_negative"]

    # 4. Consistency component: standard deviation of scores (lower = more consistent)
    if total_submissions >= 3:
        scores = [s.percentage for s in db.query(Submission.percentage).filter(
            and_(Submission.student_id == student_id,
                 Submission.status.in_(["graded", "submitted"]))
        ).all()]
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        std_dev = variance ** 0.5
        # Lower std_dev = higher consistency score (max 100)
        consistency = max(0, 100 - std_dev) * weights["consistency"]
    else:
        consistency = 50 * weights["consistency"]

    # 5. Speed component: average time efficiency
    speed_scores = []
    submissions_with_time = db.query(Submission).filter(
        and_(Submission.student_id == student_id,
             Submission.time_spent_seconds > 0,
             Submission.status.in_(["graded", "submitted"]))
    ).all()
    for sub in submissions_with_time:
        assignment = db.query(Assignment).filter(Assignment.id == sub.assignment_id).first()
        if assignment and assignment.time_limit_minutes > 0:
            max_seconds = assignment.time_limit_minutes * 60
            time_ratio = min(1, sub.time_spent_seconds / max_seconds)
            speed_score = (1 - time_ratio) * 100
            speed_scores.append(speed_score)
    avg_speed = sum(speed_scores) / len(speed_scores) if speed_scores else 50
    speed_component = avg_speed * weights["speed"]

    # 6. Streak component
    user = db.query(User).filter(User.id == student_id).first()
    streak = user.streak_days if user else 0
    streak_component = min(streak * 5, 100) * weights["streak"]  # Cap at 100

    # Final calculation
    ranking_points = (
        score_component +
        feedback_component +
        consistency -
        negative_component +
        speed_component +
        streak_component +
        total_submissions * 0.5  # Small bonus for activity volume
    )

    # Update user's ranking points
    if user:
        user.ranking_points = round(ranking_points, 2)
        user.total_score = round(avg_percentage * total_submissions / 100, 2) if total_submissions > 0 else 0
        db.commit()

    return round(ranking_points, 2)


def update_streak(db: Session, student_id: int):
    """Update student's activity streak."""
    user = db.query(User).filter(User.id == student_id).first()
    if not user:
        return

    now = datetime.now(timezone.utc)
    if user.last_activity:
        diff = (now.date() - user.last_activity.date()).days
        if diff == 1:
            user.streak_days += 1
        elif diff > 1:
            user.streak_days = 1
        # Same day: no change
    else:
        user.streak_days = 1

    user.last_activity = now
    db.commit()


def compute_leaderboard(db: Session, scope: str = "global", scope_id: int = None) -> list[dict]:
    """
    Compute and cache leaderboard rankings.

    Scopes:
    - global: all students in the platform
    - subject: students in a specific subject
    - group: students in a specific group
    """
    # Build query for relevant students
    if scope == "subject" and scope_id:
        # Students enrolled in this subject
        enrolled = db.query(Enrollment.student_id).filter(
            Enrollment.subject_id == scope_id
        ).subquery()
        students_q = db.query(User).filter(
            User.id.in_(enrolled),
            User.role == "student",
            User.is_active == True
        )
    elif scope == "group" and scope_id:
        from app.models.group import GroupMembership
        members = db.query(GroupMembership.user_id).filter(
            GroupMembership.group_id == scope_id
        ).subquery()
        students_q = db.query(User).filter(
            User.id.in_(members),
            User.role == "student",
            User.is_active == True
        )
    else:
        students_q = db.query(User).filter(
            User.role == "student",
            User.is_active == True
        )

    students = students_q.all()

    # Calculate ranking for each student
    entries = []
    for student in students:
        # Recalculate points
        points = calculate_student_ranking_points(db, student.id)

        # Get stats
        stats = db.query(
            func.avg(Submission.percentage),
            func.count(Submission.id)
        ).filter(
            Submission.student_id == student.id,
            Submission.status.in_(["graded", "submitted"])
        )

        if scope == "subject" and scope_id:
            subject_assignments = db.query(Assignment.id).filter(
                Assignment.subject_id == scope_id
            ).subquery()
            stats = stats.filter(Submission.assignment_id.in_(subject_assignments))

        result = stats.first()
        avg_pct = result[0] or 0
        completed = result[1] or 0

        entries.append({
            "user_id": student.id,
            "username": student.username,
            "full_name": student.full_name,
            "avatar_url": student.avatar_url,
            "total_score": student.total_score,
            "average_percentage": round(avg_pct, 2),
            "assignments_completed": completed,
            "ranking_points": points,
            "current_streak": student.streak_days,
        })

    # Sort by ranking_points descending
    entries.sort(key=lambda x: x["ranking_points"], reverse=True)

    # Assign ranks
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    # Cache the results
    _cache_leaderboard(db, scope, scope_id, entries)

    return entries


def _cache_leaderboard(db: Session, scope: str, scope_id: int, entries: list[dict]):
    """Cache leaderboard data."""
    # Delete old cache
    q = db.query(LeaderboardCache).filter(LeaderboardCache.scope == scope)
    if scope_id:
        q = q.filter(LeaderboardCache.scope_id == scope_id)
    q.delete(synchronize_session=False)

    for entry in entries:
        cache = LeaderboardCache(
            user_id=entry["user_id"],
            scope=scope,
            scope_id=scope_id,
            rank=entry["rank"],
            total_score=entry["total_score"],
            average_percentage=entry["average_percentage"],
            assignments_completed=entry["assignments_completed"],
            ranking_points=entry["ranking_points"],
            current_streak=entry["current_streak"],
        )
        db.add(cache)
    db.commit()


def get_cached_leaderboard(db: Session, scope: str = "global",
                           scope_id: int = None, limit: int = 50) -> list[LeaderboardCache]:
    """Get cached leaderboard."""
    q = db.query(LeaderboardCache).filter(LeaderboardCache.scope == scope)
    if scope_id:
        q = q.filter(LeaderboardCache.scope_id == scope_id)
    return q.order_by(LeaderboardCache.rank.asc()).limit(limit).all()


def get_student_rank(db: Session, student_id: int, scope: str = "global",
                     scope_id: int = None) -> Optional[int]:
    """Get a student's rank in a specific scope."""
    q = db.query(LeaderboardCache).filter(
        LeaderboardCache.user_id == student_id,
        LeaderboardCache.scope == scope
    )
    if scope_id:
        q = q.filter(LeaderboardCache.scope_id == scope_id)
    entry = q.first()
    return entry.rank if entry else None

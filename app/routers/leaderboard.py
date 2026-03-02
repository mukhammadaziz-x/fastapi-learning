"""Leaderboard & Analytics router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.analytics import (
    LeaderboardResponse, LeaderboardEntry,
    StudentAnalytics, SubjectAnalytics,
    TeacherDashboard, AdminDashboard,
)
from app.core.security import get_current_user, require_role
from app.services.ranking import compute_leaderboard, get_cached_leaderboard, get_student_rank
from app.services.analytics import (
    get_student_analytics, get_subject_analytics,
    get_teacher_dashboard, get_admin_dashboard,
)

router = APIRouter(prefix="/api/v1", tags=["Leaderboard & Analytics"])


# ============ LEADERBOARD ============

@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    scope: str = Query("global", pattern="^(global|subject|group)$"),
    scope_id: Optional[int] = None,
    refresh: bool = False,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get leaderboard rankings.

    Scopes:
    - global: Universitetdagi barcha talabalar reytingi
    - subject: Fan bo'yicha reyting (scope_id = subject_id)
    - group: Guruh bo'yicha reyting (scope_id = group_id)
    """
    if scope != "global" and scope_id is None:
        raise HTTPException(status_code=400, detail="scope_id required for non-global scope")

    if refresh:
        # Force recompute
        entries = compute_leaderboard(db, scope, scope_id)
    else:
        # Try cache first
        cached = get_cached_leaderboard(db, scope, scope_id, limit)
        if cached:
            entries = []
            for c in cached:
                from app.crud.user import get_user
                user = get_user(db, c.user_id)
                entries.append({
                    "rank": c.rank,
                    "user_id": c.user_id,
                    "username": user.username if user else "Unknown",
                    "full_name": user.full_name if user else None,
                    "avatar_url": user.avatar_url if user else None,
                    "total_score": c.total_score,
                    "average_percentage": c.average_percentage,
                    "assignments_completed": c.assignments_completed,
                    "ranking_points": c.ranking_points,
                    "current_streak": c.current_streak,
                })
        else:
            entries = compute_leaderboard(db, scope, scope_id)

    # Get my rank
    my_rank = None
    if current_user.role == "student":
        my_rank = get_student_rank(db, current_user.id, scope, scope_id)
        if my_rank is None:
            for e in entries:
                if e.get("user_id") == current_user.id:
                    my_rank = e.get("rank")
                    break

    return LeaderboardResponse(
        scope=scope,
        scope_id=scope_id,
        total_participants=len(entries),
        entries=[LeaderboardEntry(**e) for e in entries[:limit]],
        my_rank=my_rank,
    )


@router.get("/leaderboard/my-rank")
def get_my_rank(
    scope: str = Query("global", pattern="^(global|subject|group)$"),
    scope_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get current student's rank."""
    if current_user.role != "student":
        raise HTTPException(status_code=400, detail="Only students have rankings")

    rank = get_student_rank(db, current_user.id, scope, scope_id)
    if rank is None:
        # Compute fresh
        compute_leaderboard(db, scope, scope_id)
        rank = get_student_rank(db, current_user.id, scope, scope_id)

    return {
        "user_id": current_user.id,
        "scope": scope,
        "scope_id": scope_id,
        "rank": rank,
        "ranking_points": current_user.ranking_points,
    }


# ============ ANALYTICS ============

@router.get("/analytics/student/{student_id}", response_model=StudentAnalytics)
def student_analytics(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get comprehensive analytics for a student."""
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    data = get_student_analytics(db, student_id)
    if not data:
        raise HTTPException(status_code=404, detail="Student not found")
    return data


@router.get("/analytics/subject/{subject_id}", response_model=SubjectAnalytics)
def subject_analytics(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Get analytics for a subject."""
    data = get_subject_analytics(db, subject_id)
    if not data:
        raise HTTPException(status_code=404, detail="Subject not found")
    return data


@router.get("/analytics/my", response_model=StudentAnalytics)
def my_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get current user's analytics."""
    if current_user.role != "student":
        raise HTTPException(status_code=400, detail="Analytics available for students only via this endpoint")
    return get_student_analytics(db, current_user.id)


# ============ DASHBOARDS ============

@router.get("/dashboard/teacher", response_model=TeacherDashboard)
def teacher_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Get teacher dashboard."""
    teacher_id = current_user.id
    return get_teacher_dashboard(db, teacher_id)


@router.get("/dashboard/admin", response_model=AdminDashboard)
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Get admin dashboard."""
    return get_admin_dashboard(db)

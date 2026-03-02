"""Analytics service - aggregation queries and calculations."""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, case
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.user import User
from app.models.subject import Subject
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment
from app.models.submission import Submission, SubmissionAnswer
from app.models.feedback import Feedback
from app.services.ranking import get_student_rank


def get_student_analytics(db: Session, student_id: int) -> dict:
    """Comprehensive analytics for a student."""
    user = db.query(User).filter(User.id == student_id).first()
    if not user:
        return {}

    # Total assignments available
    enrolled_subjects = db.query(Enrollment.subject_id).filter(
        Enrollment.student_id == student_id
    ).scalar_subquery()
    total_assignments = db.query(func.count(Assignment.id)).filter(
        Assignment.subject_id.in_(enrolled_subjects),
        Assignment.is_published == True,
    ).scalar() or 0

    # Completed submissions
    completed = db.query(func.count(Submission.id)).filter(
        and_(Submission.student_id == student_id,
             Submission.status.in_(["graded", "submitted"]))
    ).scalar() or 0

    # Average score
    avg_data = db.query(
        func.avg(Submission.score),
        func.avg(Submission.percentage),
        func.sum(Submission.time_spent_seconds)
    ).filter(
        and_(Submission.student_id == student_id,
             Submission.status.in_(["graded", "submitted"]))
    ).first()

    avg_score = avg_data[0] or 0
    avg_pct = avg_data[1] or 0
    total_time = avg_data[2] or 0

    # Grade distribution
    grades = db.query(
        Submission.grade, func.count(Submission.id)
    ).filter(
        and_(Submission.student_id == student_id,
             Submission.grade.isnot(None))
    ).group_by(Submission.grade).all()
    grade_dist = {g: c for g, c in grades}

    # Subject scores
    subject_scores = []
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == student_id).all()
    for enrollment in enrollments:
        subject = db.query(Subject).filter(Subject.id == enrollment.subject_id).first()
        if not subject:
            continue
        subj_avg = db.query(func.avg(Submission.percentage)).join(
            Assignment, Submission.assignment_id == Assignment.id
        ).filter(
            and_(Submission.student_id == student_id,
                 Assignment.subject_id == subject.id,
                 Submission.status.in_(["graded", "submitted"]))
        ).scalar() or 0
        subject_scores.append({
            "subject_id": subject.id,
            "subject": subject.name,
            "avg_score": round(subj_avg, 2),
        })

    # Weekly activity (last 12 weeks)
    twelve_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=12)
    weekly = db.query(
        func.date_trunc('week', Submission.submitted_at).label('week'),
        func.count(Submission.id)
    ).filter(
        and_(Submission.student_id == student_id,
             Submission.submitted_at >= twelve_weeks_ago)
    ).group_by('week').order_by('week').all()
    weekly_activity = [{"week": str(w), "submissions": c} for w, c in weekly if w]

    # Feedback summary
    fb_summary = db.query(
        Feedback.feedback_type, func.count(Feedback.id)
    ).filter(Feedback.student_id == student_id).group_by(Feedback.feedback_type).all()
    feedbacks_summary = {ft: c for ft, c in fb_summary}

    # Global rank
    global_rank = get_student_rank(db, student_id, "global")

    return {
        "user_id": student_id,
        "username": user.username,
        "total_assignments": total_assignments,
        "completed_assignments": completed,
        "average_score": round(avg_score, 2),
        "average_percentage": round(avg_pct, 2),
        "total_time_spent_minutes": round(total_time / 60, 2),
        "grade_distribution": grade_dist,
        "subject_scores": subject_scores,
        "weekly_activity": weekly_activity,
        "streak_days": user.streak_days,
        "ranking_points": user.ranking_points,
        "global_rank": global_rank,
        "feedbacks_summary": feedbacks_summary,
    }


def get_subject_analytics(db: Session, subject_id: int) -> dict:
    """Analytics for a specific subject."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        return {}

    total_students = db.query(func.count(Enrollment.id)).filter(
        Enrollment.subject_id == subject_id
    ).scalar() or 0

    total_assignments = db.query(func.count(Assignment.id)).filter(
        Assignment.subject_id == subject_id
    ).scalar() or 0

    # Average score across all submissions for this subject's assignments
    avg_score = db.query(func.avg(Submission.percentage)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        and_(Assignment.subject_id == subject_id,
             Submission.status.in_(["graded", "submitted"]))
    ).scalar() or 0

    # Completion rate
    total_expected = total_students * total_assignments if total_assignments > 0 else 1
    total_completed = db.query(func.count(Submission.id)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        and_(Assignment.subject_id == subject_id,
             Submission.status.in_(["graded", "submitted"]))
    ).scalar() or 0
    completion_rate = (total_completed / total_expected * 100) if total_expected > 0 else 0

    # Grade distribution
    grades = db.query(
        Submission.grade, func.count(Submission.id)
    ).join(Assignment, Submission.assignment_id == Assignment.id).filter(
        and_(Assignment.subject_id == subject_id, Submission.grade.isnot(None))
    ).group_by(Submission.grade).all()
    grade_dist = {g: c for g, c in grades}

    # Per-assignment stats
    assignment_stats = []
    assignments = db.query(Assignment).filter(Assignment.subject_id == subject_id).all()
    for a in assignments:
        a_avg = db.query(func.avg(Submission.percentage)).filter(
            and_(Submission.assignment_id == a.id,
                 Submission.status.in_(["graded", "submitted"]))
        ).scalar() or 0
        a_count = db.query(func.count(Submission.id)).filter(
            Submission.assignment_id == a.id
        ).scalar() or 0
        assignment_stats.append({
            "assignment_id": a.id,
            "title": a.title,
            "type": a.assignment_type,
            "avg_score": round(a_avg, 2),
            "submissions": a_count,
        })

    return {
        "subject_id": subject_id,
        "subject_name": subject.name,
        "total_students": total_students,
        "total_assignments": total_assignments,
        "average_score": round(avg_score, 2),
        "completion_rate": round(completion_rate, 2),
        "grade_distribution": grade_dist,
        "assignment_stats": assignment_stats,
    }


def get_teacher_dashboard(db: Session, teacher_id: int) -> dict:
    """Dashboard data for a teacher."""
    total_subjects = db.query(func.count(Subject.id)).filter(
        Subject.teacher_id == teacher_id
    ).scalar() or 0

    teacher_subjects = db.query(Subject.id).filter(Subject.teacher_id == teacher_id).scalar_subquery()
    total_students = db.query(func.count(func.distinct(Enrollment.student_id))).filter(
        Enrollment.subject_id.in_(teacher_subjects)
    ).scalar() or 0

    total_assignments = db.query(func.count(Assignment.id)).filter(
        Assignment.teacher_id == teacher_id
    ).scalar() or 0

    # Pending manual reviews
    pending_reviews = db.query(func.count(Submission.id)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        and_(Assignment.teacher_id == teacher_id,
             Submission.status == "submitted")
    ).scalar() or 0

    # AI flagged
    ai_flagged = db.query(func.count(Submission.id)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        and_(Assignment.teacher_id == teacher_id,
             Submission.ai_flagged == True)
    ).scalar() or 0

    # Recent submissions (last 10)
    recent = db.query(Submission).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.teacher_id == teacher_id
    ).order_by(Submission.created_at.desc()).limit(10).all()

    recent_submissions = []
    for s in recent:
        student = db.query(User).filter(User.id == s.student_id).first()
        assignment = db.query(Assignment).filter(Assignment.id == s.assignment_id).first()
        recent_submissions.append({
            "submission_id": s.id,
            "student_name": student.full_name or student.username if student else "Unknown",
            "assignment_title": assignment.title if assignment else "Unknown",
            "status": s.status,
            "percentage": s.percentage,
            "grade": s.grade,
            "submitted_at": str(s.submitted_at) if s.submitted_at else None,
        })

    # Subject overview
    subjects = db.query(Subject).filter(Subject.teacher_id == teacher_id).all()
    subject_overview = []
    for s in subjects:
        student_count = db.query(func.count(Enrollment.id)).filter(
            Enrollment.subject_id == s.id
        ).scalar() or 0
        assignment_count = db.query(func.count(Assignment.id)).filter(
            Assignment.subject_id == s.id
        ).scalar() or 0
        subject_overview.append({
            "subject_id": s.id,
            "name": s.name,
            "code": s.code,
            "students": student_count,
            "assignments": assignment_count,
        })

    return {
        "teacher_id": teacher_id,
        "total_subjects": total_subjects,
        "total_students": total_students,
        "total_assignments": total_assignments,
        "pending_reviews": pending_reviews,
        "ai_flagged_count": ai_flagged,
        "recent_submissions": recent_submissions,
        "subject_overview": subject_overview,
    }


def get_admin_dashboard(db: Session) -> dict:
    """Dashboard data for admin."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_teachers = db.query(func.count(User.id)).filter(User.role == "teacher").scalar() or 0
    total_students = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    total_subjects = db.query(func.count(Subject.id)).scalar() or 0
    total_assignments = db.query(func.count(Assignment.id)).scalar() or 0
    total_submissions = db.query(func.count(Submission.id)).scalar() or 0

    now = datetime.now(timezone.utc)
    active_assignments = db.query(func.count(Assignment.id)).filter(
        and_(Assignment.start_date <= now, Assignment.end_date >= now, Assignment.is_active == True)
    ).scalar() or 0

    platform_avg = db.query(func.avg(Submission.percentage)).filter(
        Submission.status.in_(["graded", "submitted"])
    ).scalar() or 0

    # Recent registrations
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
    recent_registrations = [{
        "id": u.id, "username": u.username, "email": u.email,
        "role": u.role, "created_at": str(u.created_at)
    } for u in recent_users]

    # Top subjects by enrollment
    top = db.query(
        Subject.id, Subject.name, func.count(Enrollment.id).label('cnt')
    ).join(Enrollment, Subject.id == Enrollment.subject_id, isouter=True
    ).group_by(Subject.id, Subject.name
    ).order_by(func.count(Enrollment.id).desc()).limit(10).all()
    top_subjects = [{"id": s_id, "name": name, "enrollments": cnt} for s_id, name, cnt in top]

    return {
        "total_users": total_users,
        "total_teachers": total_teachers,
        "total_students": total_students,
        "total_subjects": total_subjects,
        "total_assignments": total_assignments,
        "total_submissions": total_submissions,
        "active_assignments": active_assignments,
        "platform_average_score": round(platform_avg, 2),
        "recent_registrations": recent_registrations,
        "top_subjects": top_subjects,
    }

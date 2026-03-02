"""Enrollment CRUD operations."""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.models.enrollment import Enrollment


def create_enrollment(db: Session, student_id: int, subject_id: int) -> Enrollment:
    enrollment = Enrollment(student_id=student_id, subject_id=subject_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def bulk_enroll(db: Session, student_ids: list[int], subject_id: int) -> list[Enrollment]:
    enrollments = []
    for sid in student_ids:
        existing = get_enrollment(db, sid, subject_id)
        if existing:
            continue
        e = Enrollment(student_id=sid, subject_id=subject_id)
        db.add(e)
        enrollments.append(e)
    db.commit()
    for e in enrollments:
        db.refresh(e)
    return enrollments


def get_enrollment(db: Session, student_id: int, subject_id: int) -> Optional[Enrollment]:
    return db.query(Enrollment).filter(
        and_(Enrollment.student_id == student_id, Enrollment.subject_id == subject_id)
    ).first()


def get_enrollments_by_student(db: Session, student_id: int) -> list[Enrollment]:
    return db.query(Enrollment).filter(Enrollment.student_id == student_id).all()


def get_enrollments_by_subject(db: Session, subject_id: int) -> list[Enrollment]:
    return db.query(Enrollment).filter(Enrollment.subject_id == subject_id).all()


def delete_enrollment(db: Session, enrollment_id: int) -> bool:
    e = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not e:
        return False
    db.delete(e)
    db.commit()
    return True


def update_enrollment_stats(db: Session, student_id: int, subject_id: int,
                            avg_score: float, completed: int, grade: str) -> Optional[Enrollment]:
    """Update cached enrollment statistics."""
    e = get_enrollment(db, student_id, subject_id)
    if not e:
        return None
    e.average_score = avg_score
    e.total_assignments_completed = completed
    e.current_grade = grade
    db.commit()
    db.refresh(e)
    return e

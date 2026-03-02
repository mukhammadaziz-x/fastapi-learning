"""Subject CRUD operations."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.models.subject import Subject
from app.models.enrollment import Enrollment
from app.schemas.subject import SubjectCreate, SubjectUpdate


def create_subject(db: Session, data: SubjectCreate, teacher_id: int) -> Subject:
    subject = Subject(
        **data.model_dump(),
        teacher_id=teacher_id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def get_subject(db: Session, subject_id: int) -> Optional[Subject]:
    return db.query(Subject).filter(Subject.id == subject_id).first()


def get_subject_by_code(db: Session, code: str) -> Optional[Subject]:
    return db.query(Subject).filter(Subject.code == code).first()


def get_subjects(db: Session, teacher_id: int = None, skip: int = 0, limit: int = 100,
                 is_active: bool = None) -> list[Subject]:
    q = db.query(Subject)
    if teacher_id:
        q = q.filter(Subject.teacher_id == teacher_id)
    if is_active is not None:
        q = q.filter(Subject.is_active == is_active)
    return q.order_by(Subject.created_at.desc()).offset(skip).limit(limit).all()


def update_subject(db: Session, subject_id: int, data: SubjectUpdate) -> Optional[Subject]:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    return subject


def delete_subject(db: Session, subject_id: int) -> bool:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        return False
    db.delete(subject)
    db.commit()
    return True


def get_enrolled_count(db: Session, subject_id: int) -> int:
    return db.query(func.count(Enrollment.id)).filter(
        Enrollment.subject_id == subject_id
    ).scalar() or 0

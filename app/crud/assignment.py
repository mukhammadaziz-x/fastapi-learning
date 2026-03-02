"""Assignment CRUD operations."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timezone

from app.models.assignment import Assignment, AssignmentQuestion
from app.models.submission import Submission
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate, QuestionCreate, QuestionUpdate


# ============ ASSIGNMENT ============

def create_assignment(db: Session, data: AssignmentCreate, teacher_id: int) -> Assignment:
    assignment = Assignment(
        **data.model_dump(),
        teacher_id=teacher_id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def get_assignment(db: Session, assignment_id: int) -> Optional[Assignment]:
    return db.query(Assignment).filter(Assignment.id == assignment_id).first()


def get_assignments_by_subject(db: Session, subject_id: int, skip: int = 0,
                                limit: int = 100, is_published: bool = None) -> list[Assignment]:
    q = db.query(Assignment).filter(Assignment.subject_id == subject_id)
    if is_published is not None:
        q = q.filter(Assignment.is_published == is_published)
    return q.order_by(Assignment.created_at.desc()).offset(skip).limit(limit).all()


def get_assignments_by_teacher(db: Session, teacher_id: int, skip: int = 0,
                                limit: int = 100) -> list[Assignment]:
    return db.query(Assignment).filter(
        Assignment.teacher_id == teacher_id
    ).order_by(Assignment.created_at.desc()).offset(skip).limit(limit).all()


def get_active_assignments_for_student(db: Session, subject_ids: list[int]) -> list[Assignment]:
    """Get published active assignments for enrolled subjects."""
    now = datetime.now(timezone.utc)
    return db.query(Assignment).filter(
        Assignment.subject_id.in_(subject_ids),
        Assignment.is_published == True,
        Assignment.is_active == True,
        Assignment.start_date <= now,
        Assignment.end_date >= now,
    ).order_by(Assignment.end_date.asc()).all()


def update_assignment(db: Session, assignment_id: int, data: AssignmentUpdate) -> Optional[Assignment]:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return assignment


def delete_assignment(db: Session, assignment_id: int) -> bool:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        return False
    db.delete(assignment)
    db.commit()
    return True


def get_assignment_submissions_count(db: Session, assignment_id: int) -> int:
    return db.query(func.count(Submission.id)).filter(
        Submission.assignment_id == assignment_id
    ).scalar() or 0


# ============ QUESTIONS ============

def create_question(db: Session, assignment_id: int, data: QuestionCreate) -> AssignmentQuestion:
    question = AssignmentQuestion(
        **data.model_dump(),
        assignment_id=assignment_id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def bulk_create_questions(db: Session, assignment_id: int, questions: list[QuestionCreate]) -> list[AssignmentQuestion]:
    created = []
    for i, q_data in enumerate(questions):
        q = AssignmentQuestion(
            **q_data.model_dump(),
            assignment_id=assignment_id,
        )
        if q.order == 1 and i > 0:
            q.order = i + 1
        db.add(q)
        created.append(q)
    db.commit()
    for q in created:
        db.refresh(q)
    return created


def get_question(db: Session, question_id: int) -> Optional[AssignmentQuestion]:
    return db.query(AssignmentQuestion).filter(AssignmentQuestion.id == question_id).first()


def get_questions_by_assignment(db: Session, assignment_id: int) -> list[AssignmentQuestion]:
    return db.query(AssignmentQuestion).filter(
        AssignmentQuestion.assignment_id == assignment_id
    ).order_by(AssignmentQuestion.order.asc()).all()


def update_question(db: Session, question_id: int, data: QuestionUpdate) -> Optional[AssignmentQuestion]:
    question = db.query(AssignmentQuestion).filter(AssignmentQuestion.id == question_id).first()
    if not question:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question


def delete_question(db: Session, question_id: int) -> bool:
    question = db.query(AssignmentQuestion).filter(AssignmentQuestion.id == question_id).first()
    if not question:
        return False
    db.delete(question)
    db.commit()
    return True

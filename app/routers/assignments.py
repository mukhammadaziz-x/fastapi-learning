"""Assignment management router."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.crud import assignment as assignment_crud
from app.crud import subject as subject_crud
from app.crud import enrollment as enrollment_crud
from app.crud import user as user_crud
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentDetailResponse, QuestionCreate, QuestionUpdate,
    QuestionResponse, QuestionStudentView,
)
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/assignments", tags=["Assignments"])


# ============ ASSIGNMENT CRUD ============

@router.post("/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Create a new assignment."""
    subject = subject_crud.get_subject(db, data.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if current_user.role == "teacher" and subject.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this subject")
    if data.start_date >= data.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    assignment = assignment_crud.create_assignment(db, data, current_user.id)
    resp = AssignmentResponse.model_validate(assignment)
    resp.questions_count = 0
    resp.submissions_count = 0
    return resp


@router.get("/", response_model=list[AssignmentResponse])
def list_assignments(
    subject_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List assignments."""
    if current_user.role == "student":
        # Students see published assignments for their enrolled subjects
        enrollments = enrollment_crud.get_enrollments_by_student(db, current_user.id)
        subject_ids = [e.subject_id for e in enrollments]
        if subject_id:
            if subject_id not in subject_ids:
                raise HTTPException(status_code=403, detail="Not enrolled in this subject")
            subject_ids = [subject_id]
        assignments = assignment_crud.get_active_assignments_for_student(db, subject_ids)
    elif current_user.role == "teacher":
        if subject_id:
            assignments = assignment_crud.get_assignments_by_subject(db, subject_id, skip, limit)
        else:
            assignments = assignment_crud.get_assignments_by_teacher(db, current_user.id, skip, limit)
    else:  # admin
        if subject_id:
            assignments = assignment_crud.get_assignments_by_subject(db, subject_id, skip, limit)
        else:
            from app.models.assignment import Assignment
            assignments = db.query(Assignment).offset(skip).limit(limit).all()

    results = []
    for a in assignments:
        resp = AssignmentResponse.model_validate(a)
        resp.questions_count = len(a.questions) if a.questions else 0
        resp.submissions_count = assignment_crud.get_assignment_submissions_count(db, a.id)
        results.append(resp)
    return results


@router.get("/{assignment_id}", response_model=AssignmentDetailResponse)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get assignment details."""
    assignment = assignment_crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    subject = subject_crud.get_subject(db, assignment.subject_id)
    teacher = user_crud.get_user(db, assignment.teacher_id)

    resp = AssignmentDetailResponse.model_validate(assignment)
    resp.questions_count = len(assignment.questions) if assignment.questions else 0
    resp.submissions_count = assignment_crud.get_assignment_submissions_count(db, assignment.id)
    resp.subject_name = subject.name if subject else None
    resp.teacher_name = teacher.full_name or teacher.username if teacher else None

    # Hide correct answers for students
    if current_user.role == "student":
        for q in resp.questions:
            q.correct_answer = None
            q.explanation = None

    from app.crud.submission import get_submission_stats
    stats = get_submission_stats(db, assignment_id)
    resp.average_score = stats["average_percentage"]
    resp.completion_rate = 0
    return resp


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Update assignment."""
    assignment = assignment_crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if current_user.role == "teacher" and assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated = assignment_crud.update_assignment(db, assignment_id, data)
    return updated


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Delete assignment."""
    assignment = assignment_crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if current_user.role == "teacher" and assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    assignment_crud.delete_assignment(db, assignment_id)


# ============ QUESTIONS ============

@router.post("/{assignment_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def add_question(
    assignment_id: int,
    data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Add a question to an assignment."""
    assignment = assignment_crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if current_user.role == "teacher" and assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return assignment_crud.create_question(db, assignment_id, data)


@router.post("/{assignment_id}/questions/bulk", response_model=list[QuestionResponse], status_code=status.HTTP_201_CREATED)
def add_questions_bulk(
    assignment_id: int,
    questions: List[QuestionCreate],
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Add multiple questions at once."""
    assignment = assignment_crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if current_user.role == "teacher" and assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return assignment_crud.bulk_create_questions(db, assignment_id, questions)


@router.get("/{assignment_id}/questions")
def get_questions(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get questions. Students see no correct answers."""
    questions = assignment_crud.get_questions_by_assignment(db, assignment_id)
    if current_user.role == "student":
        return [QuestionStudentView.model_validate(q) for q in questions]
    return [QuestionResponse.model_validate(q) for q in questions]


@router.patch("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Update a question."""
    updated = assignment_crud.update_question(db, question_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Question not found")
    return updated


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Delete a question."""
    if not assignment_crud.delete_question(db, question_id):
        raise HTTPException(status_code=404, detail="Question not found")

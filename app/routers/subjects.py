"""Subject management router."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.crud import subject as subject_crud
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectDetailResponse
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/subjects", tags=["Subjects"])


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Create a new subject (teacher/admin)."""
    if subject_crud.get_subject_by_code(db, data.code):
        raise HTTPException(status_code=400, detail="Subject code already exists")
    subject = subject_crud.create_subject(db, data, current_user.id)
    resp = SubjectResponse.model_validate(subject)
    resp.enrolled_count = 0
    return resp


@router.get("/", response_model=list[SubjectResponse])
def list_subjects(
    teacher_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List subjects. Teachers see their own; students see all active; admin sees all."""
    if current_user.role == "teacher":
        teacher_id = current_user.id
    subjects = subject_crud.get_subjects(db, teacher_id=teacher_id, skip=skip, limit=limit)
    results = []
    for s in subjects:
        resp = SubjectResponse.model_validate(s)
        resp.enrolled_count = subject_crud.get_enrolled_count(db, s.id)
        results.append(resp)
    return results


@router.get("/{subject_id}", response_model=SubjectDetailResponse)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get subject details."""
    subject = subject_crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    from app.crud import user as user_crud
    teacher = user_crud.get_user(db, subject.teacher_id)

    resp = SubjectDetailResponse.model_validate(subject)
    resp.enrolled_count = subject_crud.get_enrolled_count(db, subject_id)
    resp.teacher_name = teacher.full_name or teacher.username if teacher else None
    resp.assignments_count = len(subject.assignments) if subject.assignments else 0
    return resp


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Update subject."""
    subject = subject_crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if current_user.role == "teacher" and subject.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated = subject_crud.update_subject(db, subject_id, data)
    return updated


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Delete subject."""
    subject = subject_crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if current_user.role == "teacher" and subject.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    subject_crud.delete_subject(db, subject_id)
    return None

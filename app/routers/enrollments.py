"""Enrollment management router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import enrollment as enrollment_crud
from app.crud import subject as subject_crud
from app.crud import user as user_crud
from app.schemas.enrollment import EnrollmentCreate, BulkEnrollmentCreate, EnrollmentResponse
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/enrollments", tags=["Enrollments"])


@router.post("/", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_student(
    data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Enroll a student in a subject."""
    student = user_crud.get_user(db, data.student_id)
    if not student or student.role != "student":
        raise HTTPException(status_code=404, detail="Student not found")
    subject = subject_crud.get_subject(db, data.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Check teacher authorization
    if current_user.role == "teacher" and subject.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this subject")

    existing = enrollment_crud.get_enrollment(db, data.student_id, data.subject_id)
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled")

    # Check max students
    if subject.max_students:
        current_count = subject_crud.get_enrolled_count(db, data.subject_id)
        if current_count >= subject.max_students:
            raise HTTPException(status_code=400, detail="Subject is full")

    enrollment = enrollment_crud.create_enrollment(db, data.student_id, data.subject_id)
    resp = EnrollmentResponse.model_validate(enrollment)
    resp.student_name = student.full_name or student.username
    resp.subject_name = subject.name
    return resp


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def bulk_enroll(
    data: BulkEnrollmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Enroll multiple students in a subject."""
    subject = subject_crud.get_subject(db, data.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if current_user.role == "teacher" and subject.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    enrollments = enrollment_crud.bulk_enroll(db, data.student_ids, data.subject_id)
    return {"message": f"Enrolled {len(enrollments)} students", "count": len(enrollments)}


@router.get("/subject/{subject_id}", response_model=list[EnrollmentResponse])
def get_subject_enrollments(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Get all students enrolled in a subject."""
    enrollments = enrollment_crud.get_enrollments_by_subject(db, subject_id)
    results = []
    for e in enrollments:
        student = user_crud.get_user(db, e.student_id)
        subject = subject_crud.get_subject(db, e.subject_id)
        resp = EnrollmentResponse.model_validate(e)
        resp.student_name = student.full_name or student.username if student else None
        resp.subject_name = subject.name if subject else None
        results.append(resp)
    return results


@router.get("/student/{student_id}", response_model=list[EnrollmentResponse])
def get_student_enrollments(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all subjects a student is enrolled in."""
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    enrollments = enrollment_crud.get_enrollments_by_student(db, student_id)
    results = []
    for e in enrollments:
        subject = subject_crud.get_subject(db, e.subject_id)
        resp = EnrollmentResponse.model_validate(e)
        resp.subject_name = subject.name if subject else None
        results.append(resp)
    return results


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Remove enrollment."""
    if not enrollment_crud.delete_enrollment(db, enrollment_id):
        raise HTTPException(status_code=404, detail="Enrollment not found")

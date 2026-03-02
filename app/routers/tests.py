"""Test management routes with fullscreen monitoring and access token support."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import crud
from app.schemas.test import (
    TestCreate, TestUpdate, TestResponse, TestDetailedResponse,
    QuestionCreate, QuestionResponse, TestResultResponse, StudentAnswerCreate,
    FullscreenViolationResponse, TeacherCreate, TeacherLogin, TeacherResponse,
    StudentCreate, StudentResponse, AccessTokenCreate, AccessTokenResponse,
    AccessTokenValidation, BulkAccessTokenCreate
)

router = APIRouter(prefix="/api/v1", tags=["tests"])


router = APIRouter(prefix="/api/v1", tags=["tests"])


# ============ TEACHER ENDPOINTS ============

@router.post("/teachers/register", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED, tags=["teachers"])
def register_teacher(teacher_data: TeacherCreate, db: Session = Depends(get_db)):
    """Register a new teacher."""
    if crud.test.get_teacher_by_email(db, teacher_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.test.get_teacher_by_username(db, teacher_data.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    return crud.test.create_teacher(db, teacher_data)


@router.post("/teachers/login", tags=["teachers"])
def login_teacher(login_data: TeacherLogin, db: Session = Depends(get_db)):
    """Authenticate a teacher."""
    teacher = crud.test.authenticate_teacher(db, login_data.username, login_data.password)
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "id": teacher.id,
        "username": teacher.username,
        "email": teacher.email,
        "full_name": teacher.full_name,
        "message": "Login successful"
    }


@router.get("/teachers/{teacher_id}", response_model=TeacherResponse, tags=["teachers"])
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """Get teacher info."""
    teacher = crud.test.get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher


# ============ STUDENT ENDPOINTS ============

@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED, tags=["students"])
def create_student(student_data: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student."""
    return crud.test.create_student(db, student_data)


@router.get("/students/teacher/{teacher_id}", response_model=list[StudentResponse], tags=["students"])
def get_teacher_students(teacher_id: int, db: Session = Depends(get_db)):
    """Get all students for a teacher."""
    return crud.test.get_students_by_teacher(db, teacher_id)


@router.get("/students/{student_id}", response_model=StudentResponse, tags=["students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get student info."""
    student = crud.test.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


# ============ TEST ENDPOINTS ============

@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def create_test(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    teacher_id: int = Query(..., description="Teacher ID"),
):
    """Create a new test."""
    if test_data.start_date >= test_data.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    return crud.test.create_test(db, test_data, teacher_id)


@router.get("/tests/{test_id}", response_model=TestDetailedResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):
    """Get test information with statistics."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    from sqlalchemy import func as sqlfunc, and_
    from app.models.test import TestResult
    completed_count = db.query(sqlfunc.count()).filter(
        and_(TestResult.test_id == test_id, TestResult.status == "completed")
    ).scalar() or 0
    pending_count = db.query(sqlfunc.count()).filter(
        and_(TestResult.test_id == test_id, TestResult.status.in_(["pending", "in_progress"]))
    ).scalar() or 0

    response = TestDetailedResponse(
        **TestResponse.model_validate(test).model_dump(),
        completed_count=completed_count,
        pending_count=pending_count
    )
    return response


@router.get("/tests", response_model=list[TestResponse])
def list_teacher_tests(
    teacher_id: int = Query(..., description="Teacher ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get all tests for a teacher."""
    return crud.test.get_tests_by_teacher(db, teacher_id, skip, limit)


@router.patch("/tests/{test_id}", response_model=TestResponse)
def update_test(
    test_id: int,
    test_data: TestUpdate,
    teacher_id: int = Query(..., description="Teacher ID"),
    db: Session = Depends(get_db),
):
    """Update a test."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if test.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.test.update_test(db, test_id, test_data)


@router.delete("/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test(
    test_id: int,
    teacher_id: int = Query(..., description="Teacher ID"),
    db: Session = Depends(get_db),
):
    """Delete a test."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if test.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud.test.delete_test(db, test_id)


# ============ QUESTION ENDPOINTS ============

@router.post("/tests/{test_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    test_id: int,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
):
    """Add a question to a test."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return crud.test.create_question(db, test_id, question_data)


@router.get("/tests/{test_id}/questions", response_model=list[QuestionResponse])
def get_test_questions(
    test_id: int,
    hide_answers: bool = Query(True, description="Hide correct answers"),
    db: Session = Depends(get_db),
):
    """Get all questions for a test."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    questions = crud.test.get_questions_for_test(db, test_id)
    if hide_answers:
        for q in questions:
            q.correct_answer = None
    return questions


@router.delete("/tests/{test_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(test_id: int, question_id: int, db: Session = Depends(get_db)):
    """Delete a question."""
    if not crud.test.delete_question(db, question_id):
        raise HTTPException(status_code=404, detail="Question not found")


# ============ ACCESS TOKEN / LINK ENDPOINTS ============

@router.post("/access-tokens", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED, tags=["access-tokens"])
def create_access_token(
    token_data: AccessTokenCreate,
    db: Session = Depends(get_db),
):
    """Generate an access link/token for a student to take a test."""
    test = crud.test.get_test(db, token_data.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    student = crud.test.get_student(db, token_data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return crud.test.create_access_token(db, token_data.test_id, token_data.student_id, token_data.expires_at)


@router.post("/access-tokens/bulk", response_model=list[AccessTokenResponse], status_code=status.HTTP_201_CREATED, tags=["access-tokens"])
def create_bulk_access_tokens(
    bulk_data: BulkAccessTokenCreate,
    db: Session = Depends(get_db),
):
    """Generate access tokens for multiple students at once."""
    test = crud.test.get_test(db, bulk_data.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    tokens = []
    for student_id in bulk_data.student_ids:
        student = crud.test.get_student(db, student_id)
        if not student:
            continue
        token = crud.test.create_access_token(db, bulk_data.test_id, student_id, bulk_data.expires_at)
        tokens.append(token)
    return tokens


@router.get("/access-tokens/validate/{token}", response_model=AccessTokenValidation, tags=["access-tokens"])
def validate_access_token(token: str, db: Session = Depends(get_db)):
    """Validate an access token and return test info if valid."""
    result = crud.test.validate_access_token(db, token)
    if not result["valid"]:
        return AccessTokenValidation(valid=False, error=result["error"])

    test = result["test"]
    student = result["student"]
    return AccessTokenValidation(
        valid=True,
        test_title=test.title,
        student_name=student.name,
        test_id=test.id,
        student_id=student.id,
        time_limit_minutes=test.time_limit_minutes,
        max_fullscreen_violations=test.max_fullscreen_violations,
        total_questions=test.total_questions
    )


@router.get("/access-tokens/test/{test_id}", response_model=list[AccessTokenResponse], tags=["access-tokens"])
def get_test_access_tokens(test_id: int, db: Session = Depends(get_db)):
    """Get all access tokens for a test."""
    return crud.test.get_tokens_for_test(db, test_id)


@router.delete("/access-tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["access-tokens"])
def deactivate_access_token(token_id: int, db: Session = Depends(get_db)):
    """Deactivate an access token."""
    crud.test.deactivate_token(db, token_id)


# ============ TEST TAKING ENDPOINTS ============

@router.post("/take-test/{token}/start", response_model=TestResultResponse, status_code=status.HTTP_201_CREATED, tags=["test-taking"])
def start_test_with_token(token: str, db: Session = Depends(get_db)):
    """Student starts a test using an access token."""
    validation = crud.test.validate_access_token(db, token)
    if not validation["valid"]:
        raise HTTPException(status_code=403, detail=validation["error"])

    test = validation["test"]
    student = validation["student"]

    # Check if already taken
    existing = crud.test.get_student_test_result(db, test.id, student.id)
    if existing and existing.status in ["in_progress", "completed", "failed"]:
        if existing.status == "in_progress":
            return existing
        raise HTTPException(status_code=400, detail="You have already completed this test")

    # Mark token as used
    crud.test.use_access_token(db, token)

    return crud.test.create_test_result(db, test.id, student.id)


@router.post("/take-test/results/{result_id}/answer", response_model=TestResultResponse, tags=["test-taking"])
def submit_answer(
    result_id: int,
    answer_data: StudentAnswerCreate,
    db: Session = Depends(get_db),
):
    """Student submits an answer to a question."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    if result.status != "in_progress":
        raise HTTPException(status_code=400, detail="Test is not in progress")

    crud.test.save_student_answer(db, result_id, answer_data.question_id, answer_data)
    return crud.test.get_test_result(db, result_id)


@router.post("/take-test/results/{result_id}/violation", response_model=FullscreenViolationResponse, tags=["test-taking"])
def report_fullscreen_violation(result_id: int, db: Session = Depends(get_db)):
    """Report a fullscreen violation. Auto-fails test if max violations exceeded."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    if result.status != "in_progress":
        raise HTTPException(status_code=400, detail="Test is not in progress")

    # Record violation first
    violation = crud.test.record_fullscreen_violation(db, result_id)

    # Re-fetch to get updated count
    result = crud.test.get_test_result(db, result_id)
    test = crud.test.get_test(db, result.test_id)

    # Check if violations exceed maximum
    if result.fullscreen_violations >= test.max_fullscreen_violations:
        result.status = "failed"
        result.was_failed_for_violation = True
        result.score = 0
        result.percentage = 0
        result.completed_at = datetime.now()
        db.commit()

    return violation


@router.post("/take-test/results/{result_id}/submit", response_model=TestResultResponse, tags=["test-taking"])
def submit_test(result_id: int, db: Session = Depends(get_db)):
    """Student finishes and submits the test."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    if result.status != "in_progress":
        raise HTTPException(status_code=400, detail="Test is not in progress")
    return crud.test.submit_test(db, result_id)


@router.get("/take-test/results/{result_id}", response_model=TestResultResponse, tags=["test-taking"])
def get_test_result(result_id: int, db: Session = Depends(get_db)):
    """Get test result details."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result


@router.get("/take-test/results/{result_id}/status", tags=["test-taking"])
def get_test_status(result_id: int, db: Session = Depends(get_db)):
    """Get live status of a test attempt (violations, status, etc)."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    test = crud.test.get_test(db, result.test_id)
    return {
        "result_id": result.id,
        "status": result.status,
        "fullscreen_violations": result.fullscreen_violations,
        "max_violations": test.max_fullscreen_violations,
        "was_failed_for_violation": result.was_failed_for_violation,
        "score": result.score,
        "percentage": result.percentage,
        "answers_count": len(result.answers),
        "total_questions": test.total_questions
    }


# ============ TEACHER RESULTS ENDPOINTS ============

@router.get("/tests/{test_id}/results", response_model=list[TestResultResponse], tags=["results"])
def get_all_test_results(test_id: int, db: Session = Depends(get_db)):
    """Teacher gets all student results for a test."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return crud.test.get_test_results(db, test_id)


"""Submission router - test taking, answering, grading, feedback."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import submission as submission_crud
from app.crud import assignment as assignment_crud
from app.crud import enrollment as enrollment_crud
from app.crud import user as user_crud
from app.schemas.submission import (
    SubmissionStart, SubmissionResponse, SubmissionDetailResponse,
    AnswerSubmit, AnswerResponse, ViolationReport, ViolationResponse,
    ManualGrade, BulkManualGrade, FeedbackCreate, FeedbackResponse,
)
from app.core.security import get_current_user, require_role
from app.services.ranking import update_streak, calculate_student_ranking_points

router = APIRouter(prefix="/api/v1/submissions", tags=["Submissions"])


# ============ START / TAKE ASSIGNMENT ============

@router.post("/start", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def start_submission(
    data: SubmissionStart,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher", "student")),
):
    """Start a new submission (begin assignment attempt)."""
    assignment = assignment_crud.get_assignment(db, data.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check enrollment (for students)
    if current_user.role == "student":
        enrollment = enrollment_crud.get_enrollment(db, current_user.id, assignment.subject_id)
        if not enrollment:
            raise HTTPException(status_code=403, detail="Not enrolled in this subject")

    can_start, message = submission_crud.can_start_new_attempt(db, data.assignment_id, current_user.id)
    if not can_start:
        raise HTTPException(status_code=400, detail=message)

    submission = submission_crud.start_submission(db, data.assignment_id, current_user.id)

    # Update activity streak
    update_streak(db, current_user.id)

    return SubmissionResponse.model_validate(submission)


@router.post("/{submission_id}/answer", response_model=AnswerResponse)
def submit_answer(
    submission_id: int,
    data: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit an answer to a question."""
    submission = submission_crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.student_id != current_user.id and current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Not your submission")
    if submission.status != "in_progress":
        raise HTTPException(status_code=400, detail="Submission is not in progress")

    answer = submission_crud.save_answer(
        db, submission_id, data.question_id,
        answer_text=data.answer_text,
        answer_choice=data.answer_choice,
        answer_choices=data.answer_choices,
        answer_code=data.answer_code,
        answer_bool=data.answer_bool,
        answer_time_seconds=data.answer_time_seconds,
    )
    return AnswerResponse.model_validate(answer)


@router.post("/{submission_id}/submit", response_model=SubmissionResponse)
def finalize_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit/finalize an assignment attempt."""
    submission = submission_crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.student_id != current_user.id and current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Not your submission")
    if submission.status != "in_progress":
        raise HTTPException(status_code=400, detail="Submission is not in progress")

    result = submission_crud.submit_submission(db, submission_id)

    # Update ranking
    calculate_student_ranking_points(db, current_user.id)

    # Update enrollment stats
    assignment = assignment_crud.get_assignment(db, result.assignment_id)
    if assignment:
        _update_enrollment_after_submission(db, current_user.id, assignment.subject_id)

    return SubmissionResponse.model_validate(result)


def _update_enrollment_after_submission(db: Session, student_id: int, subject_id: int):
    """Recalculate enrollment stats after a submission."""
    from sqlalchemy import func, and_
    from app.models.submission import Submission
    from app.models.assignment import Assignment

    stats = db.query(
        func.avg(Submission.percentage),
        func.count(Submission.id)
    ).join(Assignment, Submission.assignment_id == Assignment.id).filter(
        and_(Submission.student_id == student_id,
             Assignment.subject_id == subject_id,
             Submission.status.in_(["graded", "submitted"]))
    ).first()

    avg_score = stats[0] or 0
    completed = stats[1] or 0
    grade = submission_crud.calculate_grade(avg_score)

    enrollment_crud.update_enrollment_stats(db, student_id, subject_id, avg_score, completed, grade)


# ============ VIOLATIONS ============

@router.post("/{submission_id}/violation", response_model=ViolationResponse)
def report_violation(
    submission_id: int,
    data: ViolationReport,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Report a fullscreen/tab violation."""
    submission = submission_crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.status != "in_progress":
        raise HTTPException(status_code=400, detail="Submission is not in progress")

    violation, test_failed = submission_crud.record_violation(
        db, submission_id, data.violation_type, data.details
    )
    if violation is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    resp = ViolationResponse.model_validate(violation)
    return resp


@router.get("/{submission_id}/status")
def get_submission_status(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get live status of a submission (violations, progress, etc.)."""
    submission = submission_crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    assignment = assignment_crud.get_assignment(db, submission.assignment_id)
    return {
        "submission_id": submission.id,
        "status": submission.status,
        "fullscreen_violations": submission.fullscreen_violations,
        "max_violations": assignment.max_fullscreen_violations if assignment else 0,
        "was_failed_for_violation": submission.was_failed_for_violation,
        "tab_switch_count": submission.tab_switch_count,
        "score": submission.score,
        "percentage": submission.percentage,
        "grade": submission.grade,
        "answers_count": len(submission.answers) if submission.answers else 0,
        "total_questions": len(assignment.questions) if assignment and assignment.questions else 0,
        "time_spent_seconds": submission.time_spent_seconds,
        "time_limit_minutes": assignment.time_limit_minutes if assignment else 0,
    }


# ============ GET SUBMISSIONS ============

@router.get("/my", response_model=list[SubmissionResponse])
def get_my_submissions(
    assignment_id: int = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get current user's submissions."""
    submissions = submission_crud.get_student_submissions(db, current_user.id, assignment_id)
    return [SubmissionResponse.model_validate(s) for s in submissions]


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get submission details."""
    submission = submission_crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Authorization
    if current_user.role == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == "teacher":
        assignment = assignment_crud.get_assignment(db, submission.assignment_id)
        if assignment and assignment.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    student = user_crud.get_user(db, submission.student_id)
    assignment = assignment_crud.get_assignment(db, submission.assignment_id)

    # Build violations list before model_validate to avoid ORM object coercion
    violations_list = [
        {"type": v.violation_type, "details": v.details, "detected_at": str(v.detected_at)}
        for v in (submission.violations or [])
    ]

    # Convert to dict first, then override violations
    sub_dict = {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "student_id": submission.student_id,
        "status": submission.status,
        "attempt_number": submission.attempt_number,
        "score": submission.score,
        "max_score": submission.max_score,
        "percentage": submission.percentage,
        "grade": submission.grade,
        "fullscreen_violations": submission.fullscreen_violations,
        "was_failed_for_violation": submission.was_failed_for_violation,
        "tab_switch_count": submission.tab_switch_count,
        "ai_suspicion_score": submission.ai_suspicion_score,
        "ai_flagged": submission.ai_flagged,
        "started_at": submission.started_at,
        "submitted_at": submission.submitted_at,
        "time_spent_seconds": submission.time_spent_seconds,
        "teacher_comment": submission.teacher_comment,
        "created_at": submission.created_at,
        "answers": [AnswerResponse.model_validate(a) for a in (submission.answers or [])],
        "student_name": student.full_name or student.username if student else None,
        "assignment_title": assignment.title if assignment else None,
        "violations": violations_list,
    }
    resp = SubmissionDetailResponse(**sub_dict)
    return resp


@router.get("/assignment/{assignment_id}", response_model=list[SubmissionResponse])
def get_assignment_submissions(
    assignment_id: int,
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Get all submissions for an assignment (teacher/admin)."""
    submissions = submission_crud.get_assignment_submissions(db, assignment_id, status)
    return [SubmissionResponse.model_validate(s) for s in submissions]


# ============ MANUAL GRADING (Teacher) ============

@router.post("/{submission_id}/grade", response_model=SubmissionResponse)
def manual_grade(
    submission_id: int,
    data: BulkManualGrade,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Manually grade answers (for essays, code, etc.)."""
    submission = submission_crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    for grade in data.grades:
        submission_crud.manual_grade_answer(db, grade.answer_id, grade.points, grade.comment)

    if data.submission_comment:
        submission.teacher_comment = data.submission_comment
        db.commit()

    # Refresh and recalculate ranking
    submission = submission_crud.get_submission(db, submission_id)
    calculate_student_ranking_points(db, submission.student_id)

    return SubmissionResponse.model_validate(submission)


# ============ FEEDBACK ============

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def give_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Teacher gives feedback to a student."""
    student = user_crud.get_user(db, data.student_id)
    if not student or student.role != "student":
        raise HTTPException(status_code=404, detail="Student not found")

    feedback = submission_crud.create_feedback(
        db, current_user.id, data.student_id,
        data.feedback_type, data.comment,
        data.ranking_impact, data.subject_id, data.submission_id,
    )

    # Recalculate ranking
    calculate_student_ranking_points(db, data.student_id)

    return FeedbackResponse.model_validate(feedback)


@router.get("/feedback/student/{student_id}", response_model=list[FeedbackResponse])
def get_student_feedbacks(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get feedbacks for a student."""
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    feedbacks = submission_crud.get_student_feedbacks(db, student_id)
    return [FeedbackResponse.model_validate(f) for f in feedbacks]

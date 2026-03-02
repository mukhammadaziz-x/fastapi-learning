"""Submission CRUD operations with grading logic."""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from datetime import datetime, timezone

from app.models.submission import Submission, SubmissionAnswer
from app.models.assignment import Assignment, AssignmentQuestion
from app.models.violation import FullscreenViolation
from app.models.feedback import Feedback
from app.core.config import settings


# ============ SUBMISSION ============

def start_submission(db: Session, assignment_id: int, student_id: int) -> Submission:
    """Start a new submission attempt."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    max_score = 0
    if assignment:
        max_score = sum(q.points for q in assignment.questions)

    # Count existing attempts
    attempt_count = db.query(func.count(Submission.id)).filter(
        and_(Submission.assignment_id == assignment_id, Submission.student_id == student_id)
    ).scalar() or 0

    submission = Submission(
        assignment_id=assignment_id,
        student_id=student_id,
        status="in_progress",
        attempt_number=attempt_count + 1,
        max_score=max_score,
        started_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def get_submission(db: Session, submission_id: int) -> Optional[Submission]:
    return db.query(Submission).filter(Submission.id == submission_id).first()


def get_student_submissions(db: Session, student_id: int, assignment_id: int = None) -> list[Submission]:
    q = db.query(Submission).filter(Submission.student_id == student_id)
    if assignment_id:
        q = q.filter(Submission.assignment_id == assignment_id)
    return q.order_by(Submission.created_at.desc()).all()


def get_assignment_submissions(db: Session, assignment_id: int, status: str = None) -> list[Submission]:
    q = db.query(Submission).filter(Submission.assignment_id == assignment_id)
    if status:
        q = q.filter(Submission.status == status)
    return q.order_by(Submission.submitted_at.desc().nullsfirst()).all()


def get_pending_review_submissions(db: Session, teacher_id: int, limit: int = 50) -> list[Submission]:
    """Get submissions that need teacher review (submitted status) for teacher's assignments."""
    return (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(
            Assignment.teacher_id == teacher_id,
            Submission.status == "submitted",
        )
        .order_by(Submission.submitted_at.desc())
        .limit(limit)
        .all()
    )


def get_active_submission(db: Session, assignment_id: int, student_id: int) -> Optional[Submission]:
    """Get the current in-progress submission."""
    return db.query(Submission).filter(
        and_(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student_id,
            Submission.status == "in_progress"
        )
    ).first()


def can_start_new_attempt(db: Session, assignment_id: int, student_id: int) -> tuple[bool, str]:
    """Check if student can start a new attempt."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        return False, "Assignment not found"
    if not assignment.is_active or not assignment.is_published:
        return False, "Assignment is not available"

    now = datetime.now(timezone.utc)
    if now < assignment.start_date:
        return False, "Assignment has not started yet"
    if now > assignment.end_date:
        return False, "Assignment deadline has passed"

    # Check active submission
    active = get_active_submission(db, assignment_id, student_id)
    if active:
        return False, "You have an active submission in progress"

    # Check max attempts
    attempt_count = db.query(func.count(Submission.id)).filter(
        and_(Submission.assignment_id == assignment_id, Submission.student_id == student_id)
    ).scalar() or 0
    if attempt_count >= assignment.max_attempts:
        return False, f"Maximum attempts ({assignment.max_attempts}) reached"

    return True, "OK"


# ============ ANSWERS ============

def save_answer(db: Session, submission_id: int, question_id: int,
                answer_text: str = None, answer_choice: str = None,
                answer_choices: list = None, answer_code: str = None,
                answer_bool: bool = None, answer_time_seconds: float = None) -> SubmissionAnswer:
    """Save or update a student's answer."""
    question = db.query(AssignmentQuestion).filter(AssignmentQuestion.id == question_id).first()

    # Auto-grade if possible
    is_correct = None
    points_earned = 0
    auto_graded = True
    kahoot_bonus = 0

    if question:
        if question.question_type == "multiple_choice":
            correct = question.correct_answer
            if isinstance(correct, str):
                is_correct = answer_choice and answer_choice.upper() == correct.upper()
            elif isinstance(correct, list):
                given = sorted([c.upper() for c in (answer_choices or [])])
                expected = sorted([c.upper() for c in correct])
                is_correct = given == expected
            if is_correct:
                points_earned = question.points

        elif question.question_type == "true_false":
            if question.correct_answer is not None:
                expected_bool = str(question.correct_answer).lower() in ("true", "1", "yes")
                is_correct = answer_bool == expected_bool
                if is_correct:
                    points_earned = question.points

        elif question.question_type == "fill_blank":
            if question.correct_answer and answer_text:
                correct_vals = question.correct_answer if isinstance(question.correct_answer, list) else [question.correct_answer]
                is_correct = answer_text.strip().lower() in [c.strip().lower() for c in correct_vals]
                if is_correct:
                    points_earned = question.points

        elif question.question_type == "kahoot":
            correct = question.correct_answer
            if isinstance(correct, str):
                is_correct = answer_choice and answer_choice.upper() == correct.upper()
            if is_correct:
                points_earned = question.points
                # Kahoot bonus: faster answer = more points
                if answer_time_seconds is not None and question.time_limit_seconds:
                    time_ratio = max(0, 1 - (answer_time_seconds / question.time_limit_seconds))
                    kahoot_bonus = round(question.points * 0.5 * time_ratio, 2)
                    points_earned += kahoot_bonus

        elif question.question_type in ("essay", "code"):
            # These need manual/specialized grading
            auto_graded = False
            is_correct = None

    # Check if answer already exists
    existing = db.query(SubmissionAnswer).filter(
        and_(SubmissionAnswer.submission_id == submission_id,
             SubmissionAnswer.question_id == question_id)
    ).first()

    if existing:
        existing.answer_text = answer_text
        existing.answer_choice = answer_choice
        existing.answer_choices = answer_choices
        existing.answer_code = answer_code
        existing.answer_bool = answer_bool
        existing.is_correct = is_correct
        existing.points_earned = points_earned
        existing.auto_graded = auto_graded
        existing.answer_time_seconds = answer_time_seconds
        existing.kahoot_bonus_points = kahoot_bonus
        existing.answered_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    answer = SubmissionAnswer(
        submission_id=submission_id,
        question_id=question_id,
        answer_text=answer_text,
        answer_choice=answer_choice,
        answer_choices=answer_choices,
        answer_code=answer_code,
        answer_bool=answer_bool,
        is_correct=is_correct,
        points_earned=points_earned,
        auto_graded=auto_graded,
        answer_time_seconds=answer_time_seconds,
        kahoot_bonus_points=kahoot_bonus,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def calculate_grade(percentage: float) -> str:
    """Calculate grade based on percentage.
    60%  -> PASS
    61-89% -> MERIT
    90-100% -> DISTINCTION
    < 60% -> FAIL
    """
    if percentage >= settings.DISTINCTION_THRESHOLD:
        return "DISTINCTION"
    elif percentage >= settings.MERIT_THRESHOLD:
        return "MERIT"
    elif percentage >= settings.PASS_THRESHOLD:
        return "PASS"
    else:
        return "FAIL"


def submit_submission(db: Session, submission_id: int) -> Optional[Submission]:
    """Finalize and grade a submission."""
    submission = get_submission(db, submission_id)
    if not submission:
        return None

    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()

    # Check violations
    if assignment and submission.fullscreen_violations >= assignment.max_fullscreen_violations:
        submission.status = "failed_violation"
        submission.was_failed_for_violation = True
        submission.score = 0
        submission.percentage = 0
        submission.grade = "FAIL"
        submission.submitted_at = datetime.now(timezone.utc)
        if submission.started_at:
            submission.time_spent_seconds = int(
                (datetime.now(timezone.utc) - submission.started_at).total_seconds()
            )
        db.commit()
        db.refresh(submission)
        return submission

    # Calculate score
    answers = db.query(SubmissionAnswer).filter(
        SubmissionAnswer.submission_id == submission_id
    ).all()

    total_score = sum(a.points_earned for a in answers)
    submission.score = total_score
    submission.percentage = (total_score / submission.max_score * 100) if submission.max_score > 0 else 0
    submission.grade = calculate_grade(submission.percentage)
    submission.status = "submitted"
    submission.submitted_at = datetime.now(timezone.utc)

    if submission.started_at:
        submission.time_spent_seconds = int(
            (datetime.now(timezone.utc) - submission.started_at).total_seconds()
        )

    # Check if any answers need manual grading
    needs_manual = any(not a.auto_graded for a in answers)
    if not needs_manual:
        submission.status = "graded"

    db.commit()
    db.refresh(submission)
    return submission


# ============ VIOLATIONS ============

def record_violation(db: Session, submission_id: int, violation_type: str = "left_fullscreen",
                     details: str = None) -> tuple[FullscreenViolation, bool]:
    """Record a violation. Returns (violation, test_failed)."""
    submission = get_submission(db, submission_id)
    if not submission:
        return None, False

    submission.fullscreen_violations += 1
    if violation_type == "tab_switch":
        submission.tab_switch_count += 1

    violation = FullscreenViolation(
        submission_id=submission_id,
        violation_type=violation_type,
        details=details,
    )
    db.add(violation)
    db.commit()
    db.refresh(violation)

    # Check if auto-fail
    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
    test_failed = False
    if assignment and submission.fullscreen_violations >= assignment.max_fullscreen_violations:
        submission.status = "failed_violation"
        submission.was_failed_for_violation = True
        submission.score = 0
        submission.percentage = 0
        submission.grade = "FAIL"
        submission.submitted_at = datetime.now(timezone.utc)
        db.commit()
        test_failed = True

    return violation, test_failed


# ============ MANUAL GRADING ============

def manual_grade_answer(db: Session, answer_id: int, points: float,
                        comment: str = None) -> Optional[SubmissionAnswer]:
    """Teacher manually grades an answer (for essays, code, etc.)."""
    answer = db.query(SubmissionAnswer).filter(SubmissionAnswer.id == answer_id).first()
    if not answer:
        return None
    answer.teacher_points = points
    answer.points_earned = points
    answer.teacher_comment = comment
    answer.auto_graded = False

    # Determine correctness
    question = db.query(AssignmentQuestion).filter(AssignmentQuestion.id == answer.question_id).first()
    if question:
        answer.is_correct = points >= (question.points * 0.5)  # 50%+ is considered correct

    db.commit()
    db.refresh(answer)

    # Recalculate submission score
    _recalculate_submission_score(db, answer.submission_id)
    return answer


def _recalculate_submission_score(db: Session, submission_id: int):
    """Recalculate total score after manual grading."""
    submission = get_submission(db, submission_id)
    if not submission:
        return

    answers = db.query(SubmissionAnswer).filter(
        SubmissionAnswer.submission_id == submission_id
    ).all()

    total_score = sum(a.points_earned for a in answers)
    submission.score = total_score
    submission.percentage = (total_score / submission.max_score * 100) if submission.max_score > 0 else 0
    submission.grade = calculate_grade(submission.percentage)

    # Check if all answers are graded
    all_graded = all(a.auto_graded or a.teacher_points is not None for a in answers)
    if all_graded and submission.status == "submitted":
        submission.status = "graded"

    db.commit()


# ============ FEEDBACK ============

def create_feedback(db: Session, teacher_id: int, student_id: int,
                    feedback_type: str, comment: str = None,
                    ranking_impact: float = 0, subject_id: int = None,
                    submission_id: int = None) -> Feedback:
    feedback = Feedback(
        student_id=student_id,
        teacher_id=teacher_id,
        subject_id=subject_id,
        submission_id=submission_id,
        feedback_type=feedback_type,
        comment=comment,
        ranking_impact=ranking_impact,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_student_feedbacks(db: Session, student_id: int) -> list[Feedback]:
    return db.query(Feedback).filter(
        Feedback.student_id == student_id
    ).order_by(Feedback.created_at.desc()).all()


# ============ STATISTICS ============

def get_submission_stats(db: Session, assignment_id: int) -> dict:
    """Get aggregate stats for an assignment."""
    submissions = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.status.in_(["graded", "submitted"])
    ).all()

    if not submissions:
        return {"total": 0, "average_score": 0, "average_percentage": 0,
                "grade_distribution": {}, "completion_rate": 0}

    total = len(submissions)
    avg_score = sum(s.score for s in submissions) / total
    avg_pct = sum(s.percentage for s in submissions) / total

    grade_dist = {}
    for s in submissions:
        g = s.grade or "UNGRADED"
        grade_dist[g] = grade_dist.get(g, 0) + 1

    return {
        "total": total,
        "average_score": round(avg_score, 2),
        "average_percentage": round(avg_pct, 2),
        "grade_distribution": grade_dist,
    }

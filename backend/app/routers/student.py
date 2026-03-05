from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    User, Student, TestLink, Test, Question,
    TestSession, Answer, TestStatus,
)
from app.auth import require_role, get_current_user

router = APIRouter(prefix="/student", tags=["student"])

student_required = require_role("student")

MAX_VIOLATIONS = 3


# ── Helpers ───────────────────────────────────────────────────────────────────
async def get_student_profile(user: User, db: AsyncSession) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student


async def get_valid_link(token: str, db: AsyncSession) -> TestLink:
    result = await db.execute(select(TestLink).where(TestLink.token == token))
    link = result.scalar_one_or_none()
    if not link or not link.is_active:
        raise HTTPException(status_code=404, detail="Test link not found or inactive")

    now = datetime.utcnow()
    if now < link.start_time:
        raise HTTPException(status_code=403, detail="Test has not started yet")
    if now > link.end_time:
        raise HTTPException(status_code=403, detail="Test link has expired")

    return link


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.get("/tests/{token}")
async def access_test(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(student_required),
):
    link = await get_valid_link(token, db)
    student = await get_student_profile(current_user, db)

    # Check for existing complete session
    existing_result = await db.execute(
        select(TestSession).where(
            TestSession.student_id == student.id,
            TestSession.test_link_id == link.id,
            TestSession.status != TestStatus.in_progress,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already completed this test")

    # Get or create in-progress session
    session_result = await db.execute(
        select(TestSession).where(
            TestSession.student_id == student.id,
            TestSession.test_link_id == link.id,
            TestSession.status == TestStatus.in_progress,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        session = TestSession(student_id=student.id, test_link_id=link.id)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # Load test + questions (without correct answers)
    test_result = await db.execute(select(Test).where(Test.id == link.test_id))
    test = test_result.scalar_one()
    questions_result = await db.execute(select(Question).where(Question.test_id == test.id))
    questions = questions_result.scalars().all()

    # Calculate effective timer end time
    # If test has a time_limit_minutes, timer = session.started_at + limit (or link end if sooner)
    timer_end = link.end_time
    if test.time_limit_minutes:
        from datetime import timedelta
        limit_end = session.started_at + timedelta(minutes=test.time_limit_minutes)
        timer_end = min(limit_end, link.end_time)

    return {
        "session_id": session.id,
        "test_title": test.title,
        "test_description": test.description,
        "topic": test.topic,
        "end_time": timer_end.isoformat(),
        "time_limit_minutes": test.time_limit_minutes,
        "violations_count": session.violations_count,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "options": q.options,
                "question_type": q.question_type,
                "points": q.points,
            }
            for q in questions
        ],
    }


class ViolationResponse(BaseModel):
    violations_count: int
    auto_submitted: bool
    message: str


@router.post("/tests/{token}/violation", response_model=ViolationResponse)
async def report_violation(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(student_required),
):
    link = await get_valid_link(token, db)
    student = await get_student_profile(current_user, db)

    session_result = await db.execute(
        select(TestSession).where(
            TestSession.student_id == student.id,
            TestSession.test_link_id == link.id,
            TestSession.status == TestStatus.in_progress,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Active test session not found")

    session.violations_count += 1

    if session.violations_count >= MAX_VIOLATIONS:
        session.status = TestStatus.auto_failed
        session.score = 0.0
        session.submitted_at = datetime.utcnow()
        await db.commit()
        return ViolationResponse(
            violations_count=session.violations_count,
            auto_submitted=True,
            message="Test auto-submitted due to fullscreen violations. Score: 0",
        )

    await db.commit()
    return ViolationResponse(
        violations_count=session.violations_count,
        auto_submitted=False,
        message=f"Warning {session.violations_count}/{MAX_VIOLATIONS}: Return to fullscreen",
    )


class SubmitAnswerItem(BaseModel):
    question_id: int
    chosen_answer: Optional[str] = None  # "A","B","C","D" or null


class SubmitRequest(BaseModel):
    answers: List[SubmitAnswerItem]
    force_fail: bool = False


@router.post("/tests/{token}/submit")
async def submit_test(
    token: str,
    body: SubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(student_required),
):
    link = await get_valid_link(token, db)
    student = await get_student_profile(current_user, db)

    session_result = await db.execute(
        select(TestSession).where(
            TestSession.student_id == student.id,
            TestSession.test_link_id == link.id,
            TestSession.status == TestStatus.in_progress,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")

    # Load questions
    questions_result = await db.execute(select(Question).where(Question.test_id == link.test_id))
    questions = {q.id: q for q in questions_result.scalars().all()}

    # Score calculation unconditionally
    total_points = sum(q.points for q in questions.values())
    session.total_questions = len(questions)

    if body.force_fail or session.violations_count >= MAX_VIOLATIONS:
        session.score = 0.0
        session.status = TestStatus.auto_failed
    else:
        earned_points = 0.0
        correct_answers = 0

        for answer_item in body.answers:
            q = questions.get(answer_item.question_id)
            if not q:
                continue
            answer_record = Answer(
                session_id=session.id,
                question_id=answer_item.question_id,
                chosen_answer=answer_item.chosen_answer,
            )
            db.add(answer_record)
            
            answer_val = str(answer_item.chosen_answer).strip().upper() if answer_item.chosen_answer else ""
            correct_val = str(q.correct_answer).strip().upper()
            is_correct = False
            
            import json
            if q.question_type == "matching":
                try:
                    user_dict = json.loads(answer_item.chosen_answer)
                    correct_dict = json.loads(q.correct_answer)
                    # strict dictionary match
                    if user_dict == correct_dict:
                        is_correct = True
                except:
                    pass
            elif answer_item.chosen_answer and answer_val == correct_val:
                is_correct = True
                
            if is_correct:
                earned_points += q.points
                correct_answers += 1
                
        session.correct_answers = correct_answers

        session.score = round((earned_points / total_points) * 100, 1) if total_points > 0 else 0.0
        session.status = TestStatus.passed if session.score >= 60 else TestStatus.failed

    session.submitted_at = datetime.utcnow()
    await db.commit()

    return {
        "score": session.score,
        "status": session.status.value,
        "message": "Test submitted successfully",
    }


@router.get("/stats")
async def my_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(student_required),
):
    student = await get_student_profile(current_user, db)

    sessions_result = await db.execute(
        select(TestSession, TestLink, Test)
        .join(TestLink, TestLink.id == TestSession.test_link_id)
        .join(Test, Test.id == TestLink.test_id)
        .where(
            TestSession.student_id == student.id,
            TestSession.status != TestStatus.in_progress,
        )
    )
    rows = sessions_result.all()

    sessions_out = []
    topic_scores: dict = {}

    for s, tl, t in rows:
        sessions_out.append({
            "test_title": t.title,
            "topic": t.topic,
            "score": s.score,
            "status": s.status.value,
            "violations": s.violations_count,
            "total_questions": s.total_questions,
            "correct_answers": s.correct_answers,
            "is_graded": s.is_graded,
            "teacher_grade": s.teacher_grade,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        })
        if t.topic and s.score is not None:
            topic_scores.setdefault(t.topic, []).append(s.score)

    topic_avg = {
        topic: round(sum(scores) / len(scores), 1)
        for topic, scores in topic_scores.items()
    }

    total = len(sessions_out)
    passed = sum(1 for s in sessions_out if s["status"] == "passed")

    return {
        "full_name": current_user.full_name,
        "total_tests": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round((passed / total * 100), 1) if total > 0 else 0,
        "sessions": sessions_out,
        "topic_averages": topic_avg,
    }


@router.get("/leaderboard")
async def leaderboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """
    Returns a ranked list of all students by their average score
    across passed tests. The current user's own rank is also highlighted.
    """
    sessions_result = await db.execute(
        select(TestSession, Student, User)
        .join(Student, Student.id == TestSession.student_id)
        .join(User, User.id == Student.user_id)
        .where(
            TestSession.status == TestStatus.passed,
            TestSession.score.isnot(None),
        )
    )
    rows = sessions_result.all()

    # Aggregate by student
    student_data: dict = {}
    for session, student, user in rows:
        sid = student.id
        if sid not in student_data:
            student_data[sid] = {
                "student_id": sid,
                "full_name": user.full_name,
                "scores": [],
                "tests_passed": 0,
            }
        student_data[sid]["scores"].append(session.score)
        student_data[sid]["tests_passed"] += 1

    # Build ranked list
    rankings = []
    for data in student_data.values():
        avg = round(sum(data["scores"]) / len(data["scores"]), 1)
        rankings.append({
            "student_id": data["student_id"],
            "full_name": data["full_name"],
            "avg_score": avg,
            "tests_passed": data["tests_passed"],
            "best_score": max(data["scores"]),
        })

    # Sort: by avg_score desc, then tests_passed desc
    rankings.sort(key=lambda x: (-x["avg_score"], -x["tests_passed"]))
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    # Find current student's rank
    current_student = await get_student_profile(current_user, db)
    my_rank = next((r for r in rankings if r["student_id"] == current_student.id), None)

    return {
        "rankings": rankings,
        "my_rank": my_rank,
        "total_students": len(rankings),
    }

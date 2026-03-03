import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Teacher, Test, Question, TestLink, TestSession, Student
from app.auth import require_role, get_current_user

router = APIRouter(prefix="/teacher", tags=["teacher"])

teacher_required = require_role("teacher", "admin")


# ── Schemas ────────────────────────────────────────────────────────────────────
class QuestionCreate(BaseModel):
    text: str
    options: List[str]       # ["Option A", "Option B", "Option C", "Option D"]
    correct_answer: str      # "A", "B", "C", or "D"
    points: float = 1.0


class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    topic: Optional[str] = None
    questions: Optional[List[QuestionCreate]] = None


class LinkCreate(BaseModel):
    start_time: datetime
    end_time: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────
async def get_teacher_profile(user: User, db: AsyncSession) -> Teacher:
    result = await db.execute(select(Teacher).where(Teacher.user_id == user.id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    return teacher


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.post("/tests", status_code=201)
async def create_test(
    body: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    teacher = await get_teacher_profile(current_user, db)
    test = Test(
        title=body.title,
        description=body.description,
        topic=body.topic,
        teacher_id=teacher.id,
    )
    db.add(test)
    await db.flush()

    if body.questions:
        for q in body.questions:
            question = Question(
                test_id=test.id,
                text=q.text,
                options=q.options,
                correct_answer=q.correct_answer.upper(),
                points=q.points,
            )
            db.add(question)

    await db.commit()
    await db.refresh(test)
    return {"message": "Test created", "test_id": test.id}


@router.get("/tests")
async def list_my_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    teacher = await get_teacher_profile(current_user, db)
    result = await db.execute(select(Test).where(Test.teacher_id == teacher.id, Test.is_active == True))
    tests = result.scalars().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "topic": t.topic,
            "created_at": t.created_at.isoformat(),
        }
        for t in tests
    ]


@router.post("/tests/{test_id}/questions", status_code=201)
async def add_question(
    test_id: int,
    body: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    teacher = await get_teacher_profile(current_user, db)
    result = await db.execute(select(Test).where(Test.id == test_id, Test.teacher_id == teacher.id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    question = Question(
        test_id=test_id,
        text=body.text,
        options=body.options,
        correct_answer=body.correct_answer.upper(),
        points=body.points,
    )
    db.add(question)
    await db.commit()
    return {"message": "Question added", "question_id": question.id}


@router.get("/tests/{test_id}")
async def get_test_detail(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    teacher = await get_teacher_profile(current_user, db)
    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.teacher_id == teacher.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    q_result = await db.execute(select(Question).where(Question.test_id == test_id))
    questions = q_result.scalars().all()

    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "topic": test.topic,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "points": q.points,
            }
            for q in questions
        ],
    }


@router.post("/tests/{test_id}/link", status_code=201)
async def generate_link(
    test_id: int,
    body: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    teacher = await get_teacher_profile(current_user, db)
    result = await db.execute(select(Test).where(Test.id == test_id, Test.teacher_id == teacher.id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if body.end_time <= body.start_time:
        raise HTTPException(status_code=422, detail="end_time must be after start_time")

    token = str(uuid.uuid4())
    link = TestLink(
        test_id=test_id,
        token=token,
        start_time=body.start_time,
        end_time=body.end_time,
    )
    db.add(link)
    await db.commit()

    return {
        "token": token,
        "test_link": f"/pages/test/take.html?token={token}",
        "start_time": body.start_time.isoformat(),
        "end_time": body.end_time.isoformat(),
    }


@router.get("/tests/{test_id}/results")
async def test_results(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    teacher = await get_teacher_profile(current_user, db)
    # Verify ownership
    result = await db.execute(select(Test).where(Test.id == test_id, Test.teacher_id == teacher.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Test not found")

    sessions_result = await db.execute(
        select(TestSession, Student, User)
        .join(TestLink, TestLink.id == TestSession.test_link_id)
        .join(Student, Student.id == TestSession.student_id)
        .join(User, User.id == Student.user_id)
        .where(TestLink.test_id == test_id)
    )
    rows = sessions_result.all()

    return [
        {
            "session_id": s.id,
            "student_name": u.full_name,
            "student_email": u.email,
            "score": s.score,
            "status": s.status.value,
            "violations": s.violations_count,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        }
        for s, st, u in rows
    ]


@router.get("/students/{student_id}/stats")
async def student_stats_for_teacher(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    result = await db.execute(
        select(TestSession, TestLink, Test, User, Student)
        .join(TestLink, TestLink.id == TestSession.test_link_id)
        .join(Test, Test.id == TestLink.test_id)
        .join(Student, Student.id == TestSession.student_id)
        .join(User, User.id == Student.user_id)
        .where(TestSession.student_id == student_id, TestSession.status != "in_progress")
    )
    rows = result.all()
    if not rows:
        return {"sessions": [], "topics": {}}

    student_user = rows[0][3]
    sessions_out = []
    topic_scores: dict[str, list] = {}

    for s, tl, t, u, st in rows:
        sessions_out.append({
            "test_title": t.title,
            "topic": t.topic,
            "score": s.score,
            "status": s.status.value,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        })
        if t.topic and s.score is not None:
            topic_scores.setdefault(t.topic, []).append(s.score)

    topic_avg = {topic: round(sum(scores) / len(scores), 1) for topic, scores in topic_scores.items()}

    return {
        "student_name": student_user.full_name,
        "student_email": student_user.email,
        "sessions": sessions_out,
        "topic_averages": topic_avg,
    }

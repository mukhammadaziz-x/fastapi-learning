"""Assignment & Question models - the assignment engine."""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float,
    ForeignKey, Text, func, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class Assignment(Base):
    """
    Assignment types:
    - homework: uyga vazifa
    - classwork: dars vaqtidagi vazifa
    - midterm: oraliq imtihon
    - final: yakuniy imtihon
    - practice: mashq
    - quiz: tezkor test
    """
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Assignment type
    assignment_type = Column(String(50), nullable=False, default="homework")
    # homework, classwork, midterm, final, practice, quiz

    # Exam type (overrides subject default)
    # multiple_choice, code_editor, kahoot_game, essay, mixed, fill_blank, true_false
    exam_type = Column(String(50), nullable=False, default="multiple_choice")

    # Scheduling
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Parameters
    time_limit_minutes = Column(Integer, default=60)
    max_attempts = Column(Integer, default=1)
    total_points = Column(Float, default=100)
    passing_score = Column(Float, default=60)  # percentage

    # Fullscreen monitoring
    require_fullscreen = Column(Boolean, default=True)
    max_fullscreen_violations = Column(Integer, default=3)

    # Anti-cheat
    shuffle_questions = Column(Boolean, default=True)
    shuffle_options = Column(Boolean, default=False)
    show_results_immediately = Column(Boolean, default=False)
    allow_review = Column(Boolean, default=True)

    # AI detection
    detect_ai_usage = Column(Boolean, default=True)

    # Kahoot-specific settings (JSON for flexibility)
    kahoot_settings = Column(JSON, nullable=True)
    # e.g., {"points_per_speed": true, "music": true, "time_per_question": 30}

    # Code editor settings
    code_settings = Column(JSON, nullable=True)
    # e.g., {"language": "python", "test_cases": [...], "time_limit_sec": 5}

    # Group assignment (null = all enrolled students)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subject = relationship("Subject", back_populates="assignments")
    teacher = relationship("User", back_populates="assignments_created", foreign_keys=[teacher_id])
    questions = relationship("AssignmentQuestion", back_populates="assignment", cascade="all, delete-orphan",
                             order_by="AssignmentQuestion.order")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentQuestion(Base):
    """
    Question types:
    - multiple_choice: A/B/C/D tanlov
    - true_false: To'g'ri/Noto'g'ri
    - fill_blank: Bo'sh joyni to'ldiring
    - essay: Insho / erkin javob
    - code: Kod yozish
    - kahoot: Kahoot o'yinidagi savol (tezlik muhim)
    """
    __tablename__ = "assignment_questions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)

    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="multiple_choice")
    order = Column(Integer, nullable=False, default=1)
    points = Column(Float, default=1, nullable=False)

    # Multiple choice options (JSON for flexibility - supports more than 4 options)
    options = Column(JSON, nullable=True)
    # e.g., [{"key": "A", "text": "Python"}, {"key": "B", "text": "Java"}, ...]

    # Correct answer(s) - JSON to support multiple correct answers
    correct_answer = Column(JSON, nullable=True)
    # e.g., "A" or ["A", "C"] for multiple correct

    # Essay/code specific
    max_length = Column(Integer, nullable=True)  # character limit
    rubric = Column(Text, nullable=True)  # grading rubric for essay

    # Code question specifics
    code_template = Column(Text, nullable=True)  # starter code
    test_cases = Column(JSON, nullable=True)
    # e.g., [{"input": "5", "expected_output": "25", "points": 2}, ...]
    allowed_languages = Column(JSON, nullable=True)  # ["python", "javascript"]

    # Kahoot specifics
    time_limit_seconds = Column(Integer, nullable=True)  # per-question time for kahoot
    image_url = Column(String(500), nullable=True)

    # Explanation shown after answering
    explanation = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assignment = relationship("Assignment", back_populates="questions")
    answers = relationship("SubmissionAnswer", back_populates="question", cascade="all, delete-orphan")

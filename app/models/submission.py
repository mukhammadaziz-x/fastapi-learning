"""Submission model - student's attempt at an assignment."""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float,
    ForeignKey, Text, func, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class Submission(Base):
    """A student's attempt at an assignment."""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Status tracking
    status = Column(String(50), default="in_progress", index=True)
    # in_progress, submitted, graded, failed_violation, timed_out

    # Attempt tracking
    attempt_number = Column(Integer, default=1)

    # Scores
    score = Column(Float, default=0)
    max_score = Column(Float, default=0)
    percentage = Column(Float, default=0)

    # Grade: FAIL, PASS, MERIT, DISTINCTION
    grade = Column(String(20), nullable=True)

    # Violation tracking
    fullscreen_violations = Column(Integer, default=0)
    was_failed_for_violation = Column(Boolean, default=False)
    tab_switch_count = Column(Integer, default=0)

    # AI detection
    ai_suspicion_score = Column(Float, default=0)  # 0-100
    ai_flagged = Column(Boolean, default=False)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    time_spent_seconds = Column(Integer, default=0)

    # Teacher feedback
    teacher_comment = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions", foreign_keys=[student_id])
    answers = relationship("SubmissionAnswer", back_populates="submission", cascade="all, delete-orphan")
    violations = relationship("FullscreenViolation", back_populates="submission", cascade="all, delete-orphan")


class SubmissionAnswer(Base):
    """Individual answer to a question within a submission."""
    __tablename__ = "submission_answers"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("assignment_questions.id"), nullable=False)

    # Answer content (depends on question type)
    answer_text = Column(Text, nullable=True)  # essay, fill_blank
    answer_choice = Column(String(10), nullable=True)  # multiple_choice: "A", "B", etc.
    answer_choices = Column(JSON, nullable=True)  # multiple correct: ["A", "C"]
    answer_code = Column(Text, nullable=True)  # code questions
    answer_bool = Column(Boolean, nullable=True)  # true/false

    # Grading
    is_correct = Column(Boolean, nullable=True)  # null if not yet graded (essay)
    points_earned = Column(Float, default=0)
    auto_graded = Column(Boolean, default=True)  # False for essays that need manual review

    # Code execution results
    code_output = Column(Text, nullable=True)
    code_passed_tests = Column(Integer, default=0)
    code_total_tests = Column(Integer, default=0)

    # Kahoot timing
    answer_time_seconds = Column(Float, nullable=True)
    kahoot_bonus_points = Column(Float, default=0)

    # Teacher manual grading
    teacher_points = Column(Float, nullable=True)
    teacher_comment = Column(Text, nullable=True)

    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="answers")
    question = relationship("AssignmentQuestion", back_populates="answers")

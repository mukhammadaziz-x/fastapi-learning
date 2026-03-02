from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_pwd = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tests = relationship("Test", back_populates="teacher")
    students = relationship("Student", back_populates="teacher")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="students")
    test_results = relationship("TestResult", back_populates="student")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    # Временные окна доступа
    start_date = Column(DateTime, nullable=False)  # Начало доступа
    end_date = Column(DateTime, nullable=False)    # Окончание доступа

    # Параметры теста
    total_questions = Column(Integer, default=10)
    time_limit_minutes = Column(Integer, default=60)
    max_fullscreen_violations = Column(Integer, default=3)  # Количество позволенных нарушений

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="tests")
    questions = relationship("Question", back_populates="test")
    results = relationship("TestResult", back_populates="test")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="multiple_choice")  # multiple_choice, short_answer, essay
    order = Column(Integer, nullable=False)

    # Для multiple choice
    option_a = Column(String(500), nullable=True)
    option_b = Column(String(500), nullable=True)
    option_c = Column(String(500), nullable=True)
    option_d = Column(String(500), nullable=True)
    correct_answer = Column(String(1), nullable=True)  # A, B, C, D

    points = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    test = relationship("Test", back_populates="questions")
    student_answers = relationship("StudentAnswer", back_populates="question")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    # Результаты
    score = Column(Float, default=0)
    max_score = Column(Float, default=0)
    percentage = Column(Float, default=0)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed

    # Контроль нарушений
    fullscreen_violations = Column(Integer, default=0)
    was_failed_for_violation = Column(Boolean, default=False)  # Провален ли из-за нарушений

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test = relationship("Test", back_populates="results")
    student = relationship("Student", back_populates="test_results")
    answers = relationship("StudentAnswer", back_populates="result")
    violations = relationship("FullscreenViolation", back_populates="result")


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    answer_text = Column(Text, nullable=True)  # Для short_answer и essay
    answer_choice = Column(String(1), nullable=True)  # Для multiple_choice

    is_correct = Column(Boolean, default=False)
    points_earned = Column(Integer, default=0)

    answered_at = Column(DateTime, default=datetime.utcnow)

    result = relationship("TestResult", back_populates="answers")
    question = relationship("Question", back_populates="student_answers")


class FullscreenViolation(Base):
    __tablename__ = "fullscreen_violations"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)

    violation_type = Column(String(50), default="left_fullscreen")  # left_fullscreen, inactive, etc
    violation_count = Column(Integer, default=1)

    detected_at = Column(DateTime, default=datetime.utcnow)

    result = relationship("TestResult", back_populates="violations")


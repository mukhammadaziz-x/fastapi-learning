import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey,
    Enum as SAEnum, JSON, Text, Float
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


class TestStatus(str, enum.Enum):
    in_progress = "in_progress"
    passed = "passed"
    failed = "failed"
    auto_failed = "auto_failed"


# ─── User (base for all roles) ───────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
    student_profile = relationship("Student", back_populates="user", uselist=False)


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    subject = Column(String(255), nullable=True)

    user = relationship("User", back_populates="teacher_profile")
    tests = relationship("Test", back_populates="teacher")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    student_number = Column(String(50), nullable=True)

    user = relationship("User", back_populates="student_profile")
    sessions = relationship("TestSession", back_populates="student")


# ─── Test & Questions ─────────────────────────────────────────────────────────
class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(255), nullable=True)
    time_limit_minutes = Column(Integer, nullable=True)  # None = no limit, uses link end_time
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    teacher = relationship("Teacher", back_populates="tests")
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    links = relationship("TestLink", back_populates="test", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)   # ["A. ...", "B. ...", "C. ...", "D. ..."]
    correct_answer = Column(Text, nullable=False)  # "A", "B", "C", or "D" or full text
    question_type = Column(String(50), default="multiple_choice") # multiple_choice, open_ended, true_false, matching
    points = Column(Float, default=1.0)

    test = relationship("Test", back_populates="questions")
    answers = relationship("Answer", back_populates="question")


# ─── Test Links ───────────────────────────────────────────────────────────────
class TestLink(Base):
    __tablename__ = "test_links"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    token = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test = relationship("Test", back_populates="links")
    sessions = relationship("TestSession", back_populates="test_link")


# ─── Test Sessions ────────────────────────────────────────────────────────────
class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    test_link_id = Column(Integer, ForeignKey("test_links.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    score = Column(Float, nullable=True)        # percentage 0-100
    violations_count = Column(Integer, default=0)
    status = Column(SAEnum(TestStatus), default=TestStatus.in_progress)
    
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    teacher_grade = Column(String(50), nullable=True) # Pass, Merit, Distinction
    is_graded = Column(Boolean, default=False)

    student = relationship("Student", back_populates="sessions")
    test_link = relationship("TestLink", back_populates="sessions")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    chosen_answer = Column(Text, nullable=True)  # "A","B","C","D" or full text

    session = relationship("TestSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")

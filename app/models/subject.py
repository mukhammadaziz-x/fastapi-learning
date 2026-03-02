"""Subject model - each subject has its own exam type (code, kahoot, quiz, etc.)."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "CS101"
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Exam type determines the UI/logic for assessments
    # Types: multiple_choice, code_editor, kahoot_game, essay, mixed, fill_blank, true_false
    default_exam_type = Column(String(50), nullable=False, default="multiple_choice")

    # Subject settings
    max_students = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    semester = Column(String(50), nullable=True)  # e.g., "2025-Spring"
    credit_hours = Column(Integer, default=3)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teacher = relationship("User", back_populates="subjects_created", foreign_keys=[teacher_id])
    enrollments = relationship("Enrollment", back_populates="subject", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="subject", cascade="all, delete-orphan")

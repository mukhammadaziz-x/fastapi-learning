"""Enrollment model - students enrolled in subjects."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", name="uq_enrollment_student_subject"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)

    # Accumulated stats for this enrollment
    total_assignments_completed = Column(Integer, default=0)
    average_score = Column(Float, default=0)
    current_grade = Column(String(20), default="PENDING")  # PENDING, PASS, MERIT, DISTINCTION, FAIL
    ranking_in_subject = Column(Integer, nullable=True)

    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("User", back_populates="enrollments", foreign_keys=[student_id])
    subject = relationship("Subject", back_populates="enrollments")

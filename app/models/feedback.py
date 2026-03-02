"""Feedback model - teacher feedback to students."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, func
from sqlalchemy.orm import relationship
from app.database import Base


class Feedback(Base):
    """Teacher gives feedback to a student - affects ranking."""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=True)

    # positive, negative, neutral
    feedback_type = Column(String(20), nullable=False, default="neutral")
    comment = Column(Text, nullable=True)

    # Impact on ranking (-10 to +10)
    ranking_impact = Column(Float, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", back_populates="feedbacks_received", foreign_keys=[student_id])
    teacher = relationship("User", back_populates="feedbacks_given", foreign_keys=[teacher_id])

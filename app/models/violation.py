"""Violation model - fullscreen and tab violations."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from app.database import Base


class FullscreenViolation(Base):
    __tablename__ = "fullscreen_violations"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, index=True)

    violation_type = Column(String(50), default="left_fullscreen")
    # left_fullscreen, tab_switch, window_blur, copy_paste, right_click, dev_tools
    details = Column(Text, nullable=True)  # Additional context

    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    submission = relationship("Submission", back_populates="violations")

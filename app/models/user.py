"""User model - unified for Admin, Teacher, Student with role-based access."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_pwd = Column(String(500), nullable=True)  # nullable for Google OAuth users
    role = Column(String(20), nullable=False, default="student", index=True)  # admin, teacher, student
    avatar_url = Column(String(500), nullable=True)

    # Google OAuth
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    auth_provider = Column(String(50), default="local")  # local, google

    # Student-specific fields
    student_id_number = Column(String(50), nullable=True, unique=True)  # University ID

    # Ranking / analytics
    total_score = Column(Float, default=0)
    ranking_points = Column(Float, default=0)
    streak_days = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), nullable=True)

    # Bio
    bio = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # Teacher creates subjects
    subjects_created = relationship("Subject", back_populates="teacher", foreign_keys="Subject.teacher_id")
    # Teacher creates assignments
    assignments_created = relationship("Assignment", back_populates="teacher", foreign_keys="Assignment.teacher_id")
    # Student enrollments
    enrollments = relationship("Enrollment", back_populates="student", foreign_keys="Enrollment.student_id")
    # Student submissions
    submissions = relationship("Submission", back_populates="student", foreign_keys="Submission.student_id")
    # Groups owned by teacher
    groups_owned = relationship("Group", back_populates="owner", foreign_keys="Group.owner_id")
    # Group memberships
    group_memberships = relationship("GroupMembership", back_populates="user", foreign_keys="GroupMembership.user_id")
    # Feedbacks received (for students)
    feedbacks_received = relationship("Feedback", back_populates="student", foreign_keys="Feedback.student_id")
    # Feedbacks given (by teachers)
    feedbacks_given = relationship("Feedback", back_populates="teacher", foreign_keys="Feedback.teacher_id")


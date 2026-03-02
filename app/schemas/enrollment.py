"""Enrollment schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EnrollmentCreate(BaseModel):
    student_id: int
    subject_id: int


class BulkEnrollmentCreate(BaseModel):
    student_ids: list[int]
    subject_id: int


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    total_assignments_completed: int = 0
    average_score: float = 0
    current_grade: str = "PENDING"
    ranking_in_subject: Optional[int] = None
    enrolled_at: Optional[datetime] = None
    student_name: Optional[str] = None
    subject_name: Optional[str] = None

    class Config:
        from_attributes = True

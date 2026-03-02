"""Subject schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    description: Optional[str] = None
    default_exam_type: str = Field(
        default="multiple_choice",
        pattern="^(multiple_choice|code_editor|kahoot_game|essay|mixed|fill_blank|true_false)$"
    )
    max_students: Optional[int] = None
    semester: Optional[str] = None
    credit_hours: int = 3


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_exam_type: Optional[str] = None
    max_students: Optional[int] = None
    semester: Optional[str] = None
    credit_hours: Optional[int] = None
    is_active: Optional[bool] = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    teacher_id: int
    default_exam_type: str
    max_students: Optional[int] = None
    is_active: bool
    semester: Optional[str] = None
    credit_hours: int
    created_at: Optional[datetime] = None
    enrolled_count: int = 0

    class Config:
        from_attributes = True


class SubjectDetailResponse(SubjectResponse):
    teacher_name: Optional[str] = None
    assignments_count: int = 0
    average_score: float = 0

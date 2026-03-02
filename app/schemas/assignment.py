"""Assignment & Question schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ========== QUESTION SCHEMAS ==========
class QuestionCreate(BaseModel):
    question_text: str
    question_type: str = Field(
        default="multiple_choice",
        pattern="^(multiple_choice|true_false|fill_blank|essay|code|kahoot)$"
    )
    order: int = 1
    points: float = Field(default=1, ge=0.1)
    options: Optional[List[dict]] = None
    # [{"key": "A", "text": "Python"}, {"key": "B", "text": "Java"}]
    correct_answer: Optional[Any] = None
    # "A" or ["A", "C"]
    max_length: Optional[int] = None
    rubric: Optional[str] = None
    code_template: Optional[str] = None
    test_cases: Optional[List[dict]] = None
    allowed_languages: Optional[List[str]] = None
    time_limit_seconds: Optional[int] = None
    image_url: Optional[str] = None
    explanation: Optional[str] = None


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    order: Optional[int] = None
    points: Optional[float] = None
    options: Optional[List[dict]] = None
    correct_answer: Optional[Any] = None
    max_length: Optional[int] = None
    rubric: Optional[str] = None
    code_template: Optional[str] = None
    test_cases: Optional[List[dict]] = None
    allowed_languages: Optional[List[str]] = None
    time_limit_seconds: Optional[int] = None
    image_url: Optional[str] = None
    explanation: Optional[str] = None


class QuestionResponse(BaseModel):
    id: int
    assignment_id: int
    question_text: str
    question_type: str
    order: int
    points: float
    options: Optional[List[dict]] = None
    correct_answer: Optional[Any] = None  # hidden for students
    max_length: Optional[int] = None
    code_template: Optional[str] = None
    allowed_languages: Optional[List[str]] = None
    time_limit_seconds: Optional[int] = None
    image_url: Optional[str] = None
    explanation: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuestionStudentView(BaseModel):
    """Question view for students - no correct answers."""
    id: int
    assignment_id: int
    question_text: str
    question_type: str
    order: int
    points: float
    options: Optional[List[dict]] = None
    max_length: Optional[int] = None
    code_template: Optional[str] = None
    allowed_languages: Optional[List[str]] = None
    time_limit_seconds: Optional[int] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


# ========== ASSIGNMENT SCHEMAS ==========
class AssignmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    subject_id: int
    assignment_type: str = Field(
        default="homework",
        pattern="^(homework|classwork|midterm|final|practice|quiz)$"
    )
    exam_type: str = Field(
        default="multiple_choice",
        pattern="^(multiple_choice|code_editor|kahoot_game|essay|mixed|fill_blank|true_false)$"
    )
    start_date: datetime
    end_date: datetime
    time_limit_minutes: int = Field(default=60, ge=1)
    max_attempts: int = Field(default=1, ge=1)
    total_points: float = Field(default=100, ge=1)
    passing_score: float = Field(default=60, ge=0, le=100)
    require_fullscreen: bool = True
    max_fullscreen_violations: int = Field(default=3, ge=1)
    shuffle_questions: bool = True
    shuffle_options: bool = False
    show_results_immediately: bool = False
    allow_review: bool = True
    detect_ai_usage: bool = True
    kahoot_settings: Optional[dict] = None
    code_settings: Optional[dict] = None
    group_id: Optional[int] = None
    is_published: bool = False


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignment_type: Optional[str] = None
    exam_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_limit_minutes: Optional[int] = None
    max_attempts: Optional[int] = None
    total_points: Optional[float] = None
    passing_score: Optional[float] = None
    require_fullscreen: Optional[bool] = None
    max_fullscreen_violations: Optional[int] = None
    shuffle_questions: Optional[bool] = None
    shuffle_options: Optional[bool] = None
    show_results_immediately: Optional[bool] = None
    allow_review: Optional[bool] = None
    detect_ai_usage: Optional[bool] = None
    kahoot_settings: Optional[dict] = None
    code_settings: Optional[dict] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None


class AssignmentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    subject_id: int
    teacher_id: int
    assignment_type: str
    exam_type: str
    start_date: datetime
    end_date: datetime
    time_limit_minutes: int
    max_attempts: int
    total_points: float
    passing_score: float
    require_fullscreen: bool
    max_fullscreen_violations: int
    shuffle_questions: bool
    show_results_immediately: bool
    detect_ai_usage: bool
    kahoot_settings: Optional[dict] = None
    code_settings: Optional[dict] = None
    group_id: Optional[int] = None
    is_active: bool
    is_published: bool
    questions_count: int = 0
    submissions_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssignmentDetailResponse(AssignmentResponse):
    questions: List[QuestionResponse] = []
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    average_score: float = 0
    completion_rate: float = 0

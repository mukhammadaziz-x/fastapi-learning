"""Submission schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ========== ANSWER SCHEMAS ==========
class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: Optional[str] = None  # essay, fill_blank
    answer_choice: Optional[str] = None  # "A", "B", etc.
    answer_choices: Optional[List[str]] = None  # multiple correct
    answer_code: Optional[str] = None  # code
    answer_bool: Optional[bool] = None  # true/false
    answer_time_seconds: Optional[float] = None  # kahoot timing


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: Optional[str] = None
    answer_choice: Optional[str] = None
    answer_choices: Optional[List[str]] = None
    answer_code: Optional[str] = None
    answer_bool: Optional[bool] = None
    is_correct: Optional[bool] = None
    points_earned: float = 0
    auto_graded: bool = True
    code_output: Optional[str] = None
    code_passed_tests: int = 0
    code_total_tests: int = 0
    answer_time_seconds: Optional[float] = None
    kahoot_bonus_points: float = 0
    teacher_points: Optional[float] = None
    teacher_comment: Optional[str] = None
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== SUBMISSION SCHEMAS ==========
class SubmissionStart(BaseModel):
    assignment_id: int


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    status: str
    attempt_number: int
    score: float
    max_score: float
    percentage: float
    grade: Optional[str] = None
    fullscreen_violations: int = 0
    was_failed_for_violation: bool = False
    tab_switch_count: int = 0
    ai_suspicion_score: float = 0
    ai_flagged: bool = False
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    time_spent_seconds: int = 0
    teacher_comment: Optional[str] = None
    created_at: Optional[datetime] = None
    answers: List[AnswerResponse] = []

    class Config:
        from_attributes = True


class SubmissionDetailResponse(SubmissionResponse):
    student_name: Optional[str] = None
    assignment_title: Optional[str] = None
    violations: List[dict] = []


class ViolationReport(BaseModel):
    violation_type: str = Field(
        default="left_fullscreen",
        pattern="^(left_fullscreen|tab_switch|window_blur|copy_paste|right_click|dev_tools)$"
    )
    details: Optional[str] = None


class ViolationResponse(BaseModel):
    id: int
    submission_id: int
    violation_type: str
    details: Optional[str] = None
    detected_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== GRADING SCHEMAS ==========
class ManualGrade(BaseModel):
    answer_id: int
    points: float = Field(ge=0)
    comment: Optional[str] = None


class BulkManualGrade(BaseModel):
    grades: List[ManualGrade]
    submission_comment: Optional[str] = None


# ========== FEEDBACK SCHEMAS ==========
class FeedbackCreate(BaseModel):
    student_id: int
    subject_id: Optional[int] = None
    submission_id: Optional[int] = None
    feedback_type: str = Field(
        default="neutral",
        pattern="^(positive|negative|neutral)$"
    )
    comment: Optional[str] = None
    ranking_impact: float = Field(default=0, ge=-10, le=10)


class FeedbackResponse(BaseModel):
    id: int
    student_id: int
    teacher_id: int
    subject_id: Optional[int] = None
    submission_id: Optional[int] = None
    feedback_type: str
    comment: Optional[str] = None
    ranking_impact: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ========== TEACHER SCHEMAS ==========
class TeacherBase(BaseModel):
    email: EmailStr
    username: str


class TeacherCreate(TeacherBase):
    password: str
    full_name: Optional[str] = None


class TeacherLogin(BaseModel):
    username: str
    password: str


class TeacherResponse(TeacherBase):
    id: int
    full_name: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== STUDENT SCHEMAS ==========
class StudentBase(BaseModel):
    email: EmailStr
    name: str


class StudentCreate(StudentBase):
    teacher_id: int


class StudentResponse(StudentBase):
    id: int
    teacher_id: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== QUESTION SCHEMAS ==========
class QuestionBase(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"
    order: int
    points: int = Field(default=1, ge=1)


class QuestionCreate(QuestionBase):
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None


class QuestionResponse(QuestionCreate):
    id: int
    test_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== TEST SCHEMAS ==========
class TestBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    total_questions: int = Field(default=10, ge=1)
    time_limit_minutes: int = Field(default=60, ge=5)
    max_fullscreen_violations: int = Field(default=3, ge=1)


class TestCreate(TestBase):
    pass


class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_limit_minutes: Optional[int] = None
    max_fullscreen_violations: Optional[int] = None
    is_active: Optional[bool] = None


class TestResponse(TestBase):
    id: int
    teacher_id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True


class TestDetailedResponse(TestResponse):
    """Расширенный ответ с полной информацией о тесте"""
    total_enrolled_students: int = 0
    completed_count: int = 0
    pending_count: int = 0


# ========== TEST RESULT SCHEMAS ==========
class StudentAnswerCreate(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    answer_choice: Optional[str] = None


class StudentAnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: Optional[str] = None
    answer_choice: Optional[str] = None
    is_correct: bool
    points_earned: int
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FullscreenViolationResponse(BaseModel):
    id: int
    violation_type: str
    violation_count: int
    detected_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestResultCreate(BaseModel):
    test_id: int


class TestResultResponse(BaseModel):
    id: int
    test_id: int
    student_id: int
    score: float
    max_score: float
    percentage: float
    status: str
    fullscreen_violations: int
    was_failed_for_violation: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    answers: List[StudentAnswerResponse] = []
    violations: List[FullscreenViolationResponse] = []

    class Config:
        from_attributes = True


# ========== ACCESS TOKEN / LINK SCHEMAS ==========
class TestAccessLink(BaseModel):
    """Ссылка для доступа студента к тесту"""
    test_id: int
    student_id: int
    token: str
    is_active: bool
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    test_access_link: Optional[str] = None


# ========== ACCESS TOKEN REQUEST SCHEMAS ==========
class AccessTokenCreate(BaseModel):
    test_id: int
    student_id: int
    expires_at: datetime


class AccessTokenResponse(BaseModel):
    id: int
    token: str
    test_id: int
    student_id: int
    is_active: bool
    is_used: bool
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccessTokenValidation(BaseModel):
    valid: bool
    error: Optional[str] = None
    test_title: Optional[str] = None
    student_name: Optional[str] = None
    test_id: Optional[int] = None
    student_id: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    max_fullscreen_violations: Optional[int] = None
    total_questions: Optional[int] = None


class BulkAccessTokenCreate(BaseModel):
    test_id: int
    student_ids: List[int]
    expires_at: datetime


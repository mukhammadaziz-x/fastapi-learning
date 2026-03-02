"""CRUD operations for tests, questions, results, and access tokens."""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid

from app.models.test import Test, Question, TestResult, StudentAnswer, FullscreenViolation, TestAccessToken, Teacher, Student
from app.schemas.test import TestCreate, TestUpdate, QuestionCreate, StudentAnswerCreate, TeacherCreate, StudentCreate


# ============ TEST CRUD ============

def create_test(db: Session, test_data: TestCreate, teacher_id: int) -> Test:
    """Создаёт новый тест."""
    db_test = Test(
        **test_data.model_dump(),
        teacher_id=teacher_id
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test


def get_test(db: Session, test_id: int) -> Test | None:
    """Получает тест по ID."""
    return db.query(Test).filter(Test.id == test_id).first()


def get_tests_by_teacher(db: Session, teacher_id: int, skip: int = 0, limit: int = 100) -> list[Test]:
    """Получает все тесты учителя."""
    return (
        db.query(Test)
        .filter(Test.teacher_id == teacher_id)
        .order_by(Test.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_test(db: Session, test_id: int, test_data: TestUpdate) -> Test | None:
    """Обновляет тест."""
    db_test = db.query(Test).filter(Test.id == test_id).first()
    if not db_test:
        return None

    update_data = test_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_test, field, value)

    db.commit()
    db.refresh(db_test)
    return db_test


def delete_test(db: Session, test_id: int) -> bool:
    """Удаляет тест."""
    db_test = db.query(Test).filter(Test.id == test_id).first()
    if not db_test:
        return False
    db.delete(db_test)
    db.commit()
    return True


def is_test_accessible(db: Session, test_id: int) -> bool:
    """Проверяет доступен ли тест в текущее время."""
    test = get_test(db, test_id)
    if not test or not test.is_active:
        return False

    now = datetime.now()
    return test.start_date <= now <= test.end_date


# ============ QUESTION CRUD ============

def create_question(db: Session, test_id: int, question_data: QuestionCreate) -> Question:
    """Создаёт новый вопрос в тесте."""
    db_question = Question(
        **question_data.model_dump(),
        test_id=test_id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_questions_for_test(db: Session, test_id: int) -> list[Question]:
    """Получает все вопросы теста упорядоченные по порядку."""
    return (
        db.query(Question)
        .filter(Question.test_id == test_id)
        .order_by(Question.order.asc())
        .all()
    )


def get_question(db: Session, question_id: int) -> Question | None:
    """Получает вопрос по ID."""
    return db.query(Question).filter(Question.id == question_id).first()


def delete_question(db: Session, question_id: int) -> bool:
    """Удаляет вопрос."""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        return False
    db.delete(db_question)
    db.commit()
    return True


# ============ TEST RESULT CRUD ============

def create_test_result(db: Session, test_id: int, student_id: int) -> TestResult:
    """Создаёт результат теста для студента."""
    test = get_test(db, test_id)
    max_score = sum(q.points for q in test.questions) if test else 0

    db_result = TestResult(
        test_id=test_id,
        student_id=student_id,
        status="in_progress",
        started_at=datetime.now(),
        max_score=max_score
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


def get_test_result(db: Session, result_id: int) -> TestResult | None:
    """Получает результат теста по ID."""
    return db.query(TestResult).filter(TestResult.id == result_id).first()


def get_student_test_result(db: Session, test_id: int, student_id: int) -> TestResult | None:
    """Получает результат студента для конкретного теста."""
    return (
        db.query(TestResult)
        .filter(and_(
            TestResult.test_id == test_id,
            TestResult.student_id == student_id
        ))
        .first()
    )


def get_test_results(db: Session, test_id: int) -> list[TestResult]:
    """Получает все результаты для теста."""
    return (
        db.query(TestResult)
        .filter(TestResult.test_id == test_id)
        .order_by(TestResult.completed_at.desc().nullsfirst())
        .all()
    )


def submit_test(db: Session, result_id: int) -> TestResult | None:
    """Завершает тест и вычисляет итоговый результат."""
    result = get_test_result(db, result_id)
    if not result:
        return None

    # Если было более 3 нарушений полноэкранного режима - провалить тест
    if result.fullscreen_violations > result.test.max_fullscreen_violations:
        result.status = "failed"
        result.was_failed_for_violation = True
        result.score = 0
        result.percentage = 0
        result.completed_at = datetime.now()
        db.commit()
        db.refresh(result)
        return result

    # Вычисляем итоговый результат
    answers = db.query(StudentAnswer).filter(StudentAnswer.result_id == result_id).all()
    total_score = sum(a.points_earned for a in answers)

    result.score = total_score
    result.percentage = (total_score / result.max_score * 100) if result.max_score > 0 else 0
    result.status = "completed"
    result.completed_at = datetime.now()

    db.commit()
    db.refresh(result)
    return result


def record_fullscreen_violation(db: Session, result_id: int, violation_type: str = "left_fullscreen") -> FullscreenViolation:
    """Записывает нарушение полноэкранного режима."""
    result = get_test_result(db, result_id)
    if result:
        result.fullscreen_violations += 1

    violation = FullscreenViolation(
        result_id=result_id,
        violation_type=violation_type
    )
    db.add(violation)
    db.commit()
    db.refresh(violation)
    return violation


# ============ STUDENT ANSWER CRUD ============

def save_student_answer(db: Session, result_id: int, question_id: int, answer_data: StudentAnswerCreate) -> StudentAnswer:
    """Сохраняет ответ студента на вопрос."""
    question = get_question(db, question_id)

    # Проверяем, правильный ли ответ
    is_correct = False
    points_earned = 0

    if question.question_type == "multiple_choice":
        is_correct = answer_data.answer_choice and answer_data.answer_choice.upper() == question.correct_answer
        if is_correct:
            points_earned = question.points

    # Если ответ уже существует - обновляем
    existing = (
        db.query(StudentAnswer)
        .filter(and_(
            StudentAnswer.result_id == result_id,
            StudentAnswer.question_id == question_id
        ))
        .first()
    )

    if existing:
        existing.answer_text = answer_data.answer_text
        existing.answer_choice = answer_data.answer_choice
        existing.is_correct = is_correct
        existing.points_earned = points_earned
        db.commit()
        db.refresh(existing)
        return existing

    # Создаём новый ответ
    db_answer = StudentAnswer(
        result_id=result_id,
        question_id=question_id,
        answer_text=answer_data.answer_text,
        answer_choice=answer_data.answer_choice,
        is_correct=is_correct,
        points_earned=points_earned
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer


def get_student_answers(db: Session, result_id: int) -> list[StudentAnswer]:
    """Получает все ответы студента на тесте."""
    return (
        db.query(StudentAnswer)
        .filter(StudentAnswer.result_id == result_id)
        .order_by(StudentAnswer.answered_at.desc())
        .all()
    )


# ============ TEACHER CRUD ============

def create_teacher(db: Session, teacher_data: TeacherCreate) -> Teacher:
    """Create a new teacher."""
    import bcrypt
    hashed = bcrypt.hashpw(teacher_data.password.encode(), bcrypt.gensalt()).decode()
    db_teacher = Teacher(
        email=teacher_data.email,
        username=teacher_data.username,
        hashed_pwd=hashed,
        full_name=getattr(teacher_data, 'full_name', None)
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


def get_teacher_by_email(db: Session, email: str) -> Teacher | None:
    return db.query(Teacher).filter(Teacher.email == email).first()


def get_teacher_by_username(db: Session, username: str) -> Teacher | None:
    return db.query(Teacher).filter(Teacher.username == username).first()


def get_teacher(db: Session, teacher_id: int) -> Teacher | None:
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()


def authenticate_teacher(db: Session, username: str, password: str) -> Teacher | None:
    """Authenticate a teacher by username and password."""
    import bcrypt
    teacher = get_teacher_by_username(db, username)
    if not teacher:
        return None
    if not bcrypt.checkpw(password.encode(), teacher.hashed_pwd.encode()):
        return None
    return teacher


# ============ STUDENT CRUD ============

def create_student(db: Session, student_data: StudentCreate) -> Student:
    """Create a new student."""
    db_student = Student(
        email=student_data.email,
        name=student_data.name,
        teacher_id=student_data.teacher_id
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_student(db: Session, student_id: int) -> Student | None:
    return db.query(Student).filter(Student.id == student_id).first()


def get_student_by_email(db: Session, email: str) -> Student | None:
    return db.query(Student).filter(Student.email == email).first()


def get_students_by_teacher(db: Session, teacher_id: int) -> list[Student]:
    return db.query(Student).filter(Student.teacher_id == teacher_id).all()


# ============ ACCESS TOKEN CRUD ============

def create_access_token(db: Session, test_id: int, student_id: int, expires_at: datetime) -> TestAccessToken:
    """Create an access token for a student to take a test."""
    token = TestAccessToken(
        token=str(uuid.uuid4()),
        test_id=test_id,
        student_id=student_id,
        expires_at=expires_at,
        is_active=True,
        is_used=False,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_access_token(db: Session, token: str) -> TestAccessToken | None:
    """Retrieve an access token by its value."""
    return db.query(TestAccessToken).filter(TestAccessToken.token == token).first()


def validate_access_token(db: Session, token: str) -> dict:
    """Validate an access token and return details."""
    access_token = get_access_token(db, token)
    if not access_token:
        return {"valid": False, "error": "Token not found"}

    if not access_token.is_active:
        return {"valid": False, "error": "Token is deactivated"}

    if access_token.is_used:
        return {"valid": False, "error": "Token has already been used"}

    now = datetime.now()
    if now > access_token.expires_at:
        return {"valid": False, "error": "Token has expired"}

    test = get_test(db, access_token.test_id)
    if not test or not test.is_active:
        return {"valid": False, "error": "Test is not available"}

    if now < test.start_date or now > test.end_date:
        return {"valid": False, "error": "Test is not accessible at this time"}

    return {
        "valid": True,
        "token": access_token,
        "test": test,
        "student": access_token.student
    }


def use_access_token(db: Session, token: str) -> TestAccessToken | None:
    """Mark an access token as used."""
    access_token = get_access_token(db, token)
    if access_token:
        access_token.is_used = True
        db.commit()
        db.refresh(access_token)
    return access_token


def get_tokens_for_test(db: Session, test_id: int) -> list[TestAccessToken]:
    """Get all access tokens for a test."""
    return db.query(TestAccessToken).filter(TestAccessToken.test_id == test_id).all()


def deactivate_token(db: Session, token_id: int) -> TestAccessToken | None:
    """Deactivate an access token."""
    access_token = db.query(TestAccessToken).filter(TestAccessToken.id == token_id).first()
    if access_token:
        access_token.is_active = False
        db.commit()
        db.refresh(access_token)
    return access_token


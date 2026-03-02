"""Test management routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import crud
from app.schemas.test import (
    TestCreate, TestUpdate, TestResponse, TestDetailedResponse,
    QuestionCreate, QuestionResponse, TestResultResponse, StudentAnswerCreate,
    FullscreenViolationResponse
)

router = APIRouter(prefix="/api/v1/tests", tags=["tests"])


# ============ TEST ENDPOINTS ============

@router.post("/", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def create_test(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    current_teacher_id: int = 1,  # В реальном приложении получаем из JWT токена
):
    """Создаёт новый тест."""
    # Проверяем валидность дат
    if test_data.start_date >= test_data.end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before end date"
        )

    test = crud.test.create_test(db, test_data, current_teacher_id)
    return test


@router.get("/{test_id}", response_model=TestDetailedResponse)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
):
    """Получает информацию о тесте."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Получаем статистику
    from sqlalchemy import func, and_
    completed_count = db.query(func.count()).filter(
        and_(
            crud.test.TestResult.test_id == test_id,
            crud.test.TestResult.status == "completed"
        )
    ).scalar() or 0

    pending_count = db.query(func.count()).filter(
        and_(
            crud.test.TestResult.test_id == test_id,
            crud.test.TestResult.status == "pending"
        )
    ).scalar() or 0

    response = TestDetailedResponse(
        **TestResponse.model_validate(test).dict(),
        completed_count=completed_count,
        pending_count=pending_count
    )
    return response


@router.get("", response_model=list[TestResponse])
def list_teacher_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_teacher_id: int = 1,  # В реальном приложении получаем из JWT токена
):
    """Получает все тесты учителя."""
    tests = crud.test.get_tests_by_teacher(db, current_teacher_id, skip, limit)
    return tests


@router.patch("/{test_id}", response_model=TestResponse)
def update_test(
    test_id: int,
    test_data: TestUpdate,
    db: Session = Depends(get_db),
    current_teacher_id: int = 1,
):
    """Обновляет тест."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.teacher_id != current_teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    updated_test = crud.test.update_test(db, test_id, test_data)
    return updated_test


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_teacher_id: int = 1,
):
    """Удаляет тест."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.teacher_id != current_teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not crud.test.delete_test(db, test_id):
        raise HTTPException(status_code=404, detail="Test not found")


# ============ QUESTION ENDPOINTS ============

@router.post("/{test_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    test_id: int,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_teacher_id: int = 1,
):
    """Добавляет вопрос в тест."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.teacher_id != current_teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    question = crud.test.create_question(db, test_id, question_data)
    return question


@router.get("/{test_id}/questions", response_model=list[QuestionResponse])
def get_test_questions(
    test_id: int,
    db: Session = Depends(get_db),
):
    """Получает все вопросы теста."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Проверяем доступность теста
    if not crud.test.is_test_accessible(db, test_id):
        raise HTTPException(
            status_code=403,
            detail="Test is not accessible at this time"
        )

    questions = crud.test.get_questions_for_test(db, test_id)
    # Не показываем правильные ответы студентам
    for q in questions:
        q.correct_answer = None
    return questions


@router.delete("/{test_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    test_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_teacher_id: int = 1,
):
    """Удаляет вопрос из теста."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.teacher_id != current_teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not crud.test.delete_question(db, question_id):
        raise HTTPException(status_code=404, detail="Question not found")


# ============ TEST TAKING ENDPOINTS ============

@router.post("/{test_id}/start", response_model=TestResultResponse, status_code=status.HTTP_201_CREATED)
def start_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_student_id: int = 1,  # В реальном приложении получаем из JWT токена
):
    """Студент начинает тест."""
    # Проверяем доступность теста
    if not crud.test.is_test_accessible(db, test_id):
        raise HTTPException(
            status_code=403,
            detail="Test is not accessible at this time"
        )

    # Проверяем, не уже ли студент сдаёт этот тест
    existing_result = crud.test.get_student_test_result(db, test_id, current_student_id)
    if existing_result and existing_result.status in ["in_progress", "completed"]:
        raise HTTPException(
            status_code=400,
            detail="Student has already taken or is taking this test"
        )

    result = crud.test.create_test_result(db, test_id, current_student_id)
    return result


@router.post("/{test_id}/results/{result_id}/answer", response_model=TestResultResponse)
def submit_answer(
    test_id: int,
    result_id: int,
    answer_data: StudentAnswerCreate,
    db: Session = Depends(get_db),
    current_student_id: int = 1,
):
    """Студент отправляет ответ на вопрос."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")

    if result.student_id != current_student_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if result.status != "in_progress":
        raise HTTPException(status_code=400, detail="Test is not in progress")

    # Сохраняем ответ
    crud.test.save_student_answer(db, result_id, answer_data.question_id, answer_data)

    # Возвращаем обновленный результат
    return crud.test.get_test_result(db, result_id)


@router.post("/{test_id}/results/{result_id}/violation", response_model=FullscreenViolationResponse)
def report_fullscreen_violation(
    test_id: int,
    result_id: int,
    db: Session = Depends(get_db),
    current_student_id: int = 1,
):
    """Студент или система сообщает о нарушении полноэкранного режима."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")

    if result.student_id != current_student_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if result.status != "in_progress":
        raise HTTPException(status_code=400, detail="Test is not in progress")

    # Проверяем количество нарушений
    test = crud.test.get_test(db, test_id)
    if result.fullscreen_violations >= test.max_fullscreen_violations:
        # Провалить тест
        result.status = "failed"
        result.was_failed_for_violation = True
        result.score = 0
        result.percentage = 0
        result.completed_at = datetime.utcnow()
        db.commit()

        raise HTTPException(
            status_code=400,
            detail=f"Test failed due to {result.fullscreen_violations} fullscreen violations"
        )

    violation = crud.test.record_fullscreen_violation(db, result_id)
    return violation


@router.post("/{test_id}/results/{result_id}/submit", response_model=TestResultResponse)
def submit_test(
    test_id: int,
    result_id: int,
    db: Session = Depends(get_db),
    current_student_id: int = 1,
):
    """Студент завершает тест."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")

    if result.student_id != current_student_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if result.status != "in_progress":
        raise HTTPException(status_code=400, detail="Test is not in progress")

    # Завершаем тест
    completed_result = crud.test.submit_test(db, result_id)
    return completed_result


@router.get("/{test_id}/results/{result_id}", response_model=TestResultResponse)
def get_test_result(
    test_id: int,
    result_id: int,
    db: Session = Depends(get_db),
    current_student_id: int = 1,
):
    """Студент получает результаты теста."""
    result = crud.test.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")

    if result.student_id != current_student_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return result


@router.get("/{test_id}/results", response_model=list[TestResultResponse])
def get_test_results(
    test_id: int,
    db: Session = Depends(get_db),
    current_teacher_id: int = 1,
):
    """Учитель получает результаты студентов для теста."""
    test = crud.test.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.teacher_id != current_teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    results = crud.test.get_test_results(db, test_id)
    return results


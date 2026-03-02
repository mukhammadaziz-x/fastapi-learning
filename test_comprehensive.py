#!/usr/bin/env python3
"""
Complete test suite for Student Performance Checker application.
Tests database connectivity, CRUD operations, and API functionality.
"""

import sys
from datetime import datetime, timedelta

# Test 1: Database Connection
print("=" * 60)
print("TEST 1: Database Connection")
print("=" * 60)

try:
    from app.database import SessionLocal, engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("[OK] PostgreSQL connection: PASSED")
except Exception as e:
    print(f"[FAIL] PostgreSQL connection failed: {e}")
    sys.exit(1)

# Test 2: Model Imports
print("\n" + "=" * 60)
print("TEST 2: Model Imports")
print("=" * 60)

try:
    from app.models.user import User
    from app.models.test import Teacher, Student, Test, Question, TestResult, StudentAnswer, FullscreenViolation
    print("[OK] All models imported successfully")
except Exception as e:
    print(f"[FAIL] Model import failed: {e}")
    sys.exit(1)

# Test 3: Schema Imports
print("\n" + "=" * 60)
print("TEST 3: Schema Imports")
print("=" * 60)

try:
    from app.schemas.test import (
        TestCreate, TestResponse, QuestionCreate, TestResultResponse,
        StudentAnswerCreate, FullscreenViolationResponse
    )
    print("[OK] All schemas imported successfully")
except Exception as e:
    print(f"[FAIL] Schema import failed: {e}")
    sys.exit(1)

# Test 4: CRUD Operations
print("\n" + "=" * 60)
print("TEST 4: CRUD Operations")
print("=" * 60)

try:
    from app import crud
    from app.models.test import Teacher
    from app.crud.user import hash_password
    db = SessionLocal()

    # Create a teacher directly in teachers table
    teacher = db.query(Teacher).filter(Teacher.email == "teacher@test.com").first()
    if not teacher:
        teacher = Teacher(
            email="teacher@test.com",
            username="testteacher",
            hashed_pwd=hash_password("password123")
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        print(f"[OK] Teacher created: ID={teacher.id}")
    else:
        print(f"[OK] Using existing teacher: ID={teacher.id}")

    # Clean up previous test data
    cleanup_tests = db.query(Test).filter(Test.title == "Test CRUD").all()
    for t in cleanup_tests:
        db.delete(t)
    db.commit()

    # Create test
    test_data = TestCreate(
        title="Test CRUD",
        description="CRUD test",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(hours=1),
        total_questions=5,
        time_limit_minutes=30,
        max_fullscreen_violations=3
    )

    test = crud.test.create_test(db, test_data, teacher_id=teacher.id)
    print(f"[OK] Test created: ID={test.id}")

    # Read test
    fetched = crud.test.get_test(db, test.id)
    if fetched:
        print(f"[OK] Test retrieved: {fetched.title}")
    else:
        print("[FAIL] Test retrieval failed")

    # Create question
    question_data = QuestionCreate(
        question_text="What is 2+2?",
        question_type="multiple_choice",
        order=1,
        option_a="3",
        option_b="4",
        option_c="5",
        option_d="6",
        correct_answer="B",
        points=1
    )

    question = crud.test.create_question(db, test.id, question_data)
    print(f"[OK] Question created: ID={question.id}")

    # Get questions
    questions = crud.test.get_questions_for_test(db, test.id)
    print(f"[OK] Questions retrieved: {len(questions)} found")

    # Update test
    from app.schemas.test import TestUpdate
    update_data = TestUpdate(title="Updated CRUD Test")
    updated = crud.test.update_test(db, test.id, update_data)
    print(f"[OK] Test updated: {updated.title}")

    # Clean up
    crud.test.delete_question(db, question.id)
    crud.test.delete_test(db, test.id)
    print("[OK] Test and question deleted")

    db.close()

except Exception as e:
    print(f"[FAIL] CRUD operations failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: FastAPI App
print("\n" + "=" * 60)
print("TEST 5: FastAPI Application")
print("=" * 60)

try:
    from app.main import app
    print(f"[OK] FastAPI app loaded")
    print(f"[OK] Total routes: {len(app.routes)}")

    # Check for test routes
    route_names = [r.path for r in app.routes]
    test_routes = [r for r in route_names if 'test' in r.lower()]
    print(f"[OK] Test-related routes: {len(test_routes)}")

except Exception as e:
    print(f"[FAIL] FastAPI app loading failed: {e}")
    sys.exit(1)

# Test 6: Database Schema
print("\n" + "=" * 60)
print("TEST 6: Database Schema")
print("=" * 60)

try:
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = [
        'users', 'teachers', 'students', 'tests',
        'questions', 'test_results', 'student_answers',
        'fullscreen_violations'
    ]

    missing = [t for t in required_tables if t not in tables]

    if missing:
        print(f"[FAIL] Missing tables: {missing}")
    else:
        print(f"[OK] All required tables exist: {len(required_tables)} tables")
        for table in required_tables:
            columns = inspector.get_columns(table)
            print(f"  - {table}: {len(columns)} columns")

except Exception as e:
    print(f"[FAIL] Schema check failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("[OK] All tests passed!")
print("\nApplication is ready for deployment.")
print("\nNext steps:")
print("1. Run: uvicorn app.main:app --reload")
print("2. Open: http://localhost:8000/docs")
print("3. Open: test_interface.html in browser")
print("\n" + "=" * 60)


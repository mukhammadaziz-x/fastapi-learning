"""Create test management tables

Revision ID: 4c5d6e7f8g9h
Revises: 3a4b5c6d7e8f
Create Date: 2026-03-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "4c5d6e7f8g9h"
down_revision = "3a4b5c6d7e8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create teachers table
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_pwd", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teachers_email", "teachers", ["email"], unique=True)
    op.create_index("ix_teachers_id", "teachers", ["id"])

    # Create students table
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_students_email", "students", ["email"])
    op.create_index("ix_students_id", "students", ["id"])

    # Create tests table
    op.create_table(
        "tests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("total_questions", sa.Integer(), default=10),
        sa.Column("time_limit_minutes", sa.Integer(), default=60),
        sa.Column("max_fullscreen_violations", sa.Integer(), default=3),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tests_id", "tests", ["id"])
    op.create_index("ix_tests_teacher_id", "tests", ["teacher_id"])

    # Create questions table
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(50), default="multiple_choice"),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("option_a", sa.String(500), nullable=True),
        sa.Column("option_b", sa.String(500), nullable=True),
        sa.Column("option_c", sa.String(500), nullable=True),
        sa.Column("option_d", sa.String(500), nullable=True),
        sa.Column("correct_answer", sa.String(1), nullable=True),
        sa.Column("points", sa.Integer(), default=1),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_id", "questions", ["id"])
    op.create_index("ix_questions_test_id", "questions", ["test_id"])

    # Create test_results table
    op.create_table(
        "test_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), default=0),
        sa.Column("max_score", sa.Float(), default=0),
        sa.Column("percentage", sa.Float(), default=0),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("fullscreen_violations", sa.Integer(), default=0),
        sa.Column("was_failed_for_violation", sa.Boolean(), default=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_test_results_id", "test_results", ["id"])
    op.create_index("ix_test_results_test_id", "test_results", ["test_id"])
    op.create_index("ix_test_results_student_id", "test_results", ["student_id"])

    # Create student_answers table
    op.create_table(
        "student_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("result_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("answer_choice", sa.String(1), nullable=True),
        sa.Column("is_correct", sa.Boolean(), default=False),
        sa.Column("points_earned", sa.Integer(), default=0),
        sa.Column("answered_at", sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(["result_id"], ["test_results.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_answers_id", "student_answers", ["id"])
    op.create_index("ix_student_answers_result_id", "student_answers", ["result_id"])

    # Create fullscreen_violations table
    op.create_table(
        "fullscreen_violations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("result_id", sa.Integer(), nullable=False),
        sa.Column("violation_type", sa.String(50), default="left_fullscreen"),
        sa.Column("violation_count", sa.Integer(), default=1),
        sa.Column("detected_at", sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(["result_id"], ["test_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fullscreen_violations_id", "fullscreen_violations", ["id"])
    op.create_index("ix_fullscreen_violations_result_id", "fullscreen_violations", ["result_id"])


def downgrade() -> None:
    op.drop_index("ix_fullscreen_violations_result_id", table_name="fullscreen_violations")
    op.drop_index("ix_fullscreen_violations_id", table_name="fullscreen_violations")
    op.drop_table("fullscreen_violations")

    op.drop_index("ix_student_answers_result_id", table_name="student_answers")
    op.drop_index("ix_student_answers_id", table_name="student_answers")
    op.drop_table("student_answers")

    op.drop_index("ix_test_results_student_id", table_name="test_results")
    op.drop_index("ix_test_results_test_id", table_name="test_results")
    op.drop_index("ix_test_results_id", table_name="test_results")
    op.drop_table("test_results")

    op.drop_index("ix_questions_test_id", table_name="questions")
    op.drop_index("ix_questions_id", table_name="questions")
    op.drop_table("questions")

    op.drop_index("ix_tests_teacher_id", table_name="tests")
    op.drop_index("ix_tests_id", table_name="tests")
    op.drop_table("tests")

    op.drop_index("ix_students_id", table_name="students")
    op.drop_index("ix_students_email", table_name="students")
    op.drop_table("students")

    op.drop_index("ix_teachers_id", table_name="teachers")
    op.drop_index("ix_teachers_email", table_name="teachers")
    op.drop_table("teachers")


"""Add test_access_tokens table and teacher full_name

Revision ID: 5d6e7f8g9h0i
Revises: 4c5d6e7f8g9h
Create Date: 2026-03-02 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '5d6e7f8g9h0i'
down_revision: Union[str, None] = '4c5d6e7f8g9h'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add full_name to teachers
    op.add_column('teachers', sa.Column('full_name', sa.String(255), nullable=True))

    # Create test_access_tokens table
    op.create_table(
        'test_access_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('token', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('test_id', sa.Integer(), sa.ForeignKey('tests.id'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_used', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('test_access_tokens')
    op.drop_column('teachers', 'full_name')

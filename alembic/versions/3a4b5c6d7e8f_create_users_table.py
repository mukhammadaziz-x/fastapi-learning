from alembic import op
import sqlalchemy as sa

# Auto-managed revision IDs
revision  = "3a4b5c6d7e8f"
down_revision = None          # None = first migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id",         sa.Integer(),     primary_key=True),
        sa.Column("email",      sa.String(255),   nullable=False),
        sa.Column("username",   sa.String(100),   nullable=False),
        sa.Column("hashed_pwd", sa.String(),      nullable=False),
        sa.Column("is_active",  sa.Boolean(),     default=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"])

def downgrade() -> None:
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
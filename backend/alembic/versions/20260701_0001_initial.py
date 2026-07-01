"""initial schema

Revision ID: 20260701_0001
Revises:
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("operation_type_hint", sa.String(16)),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"])
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Uuid(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("operation_type", sa.String(16), nullable=False),
        sa.Column("occurred_at", sa.Date(), nullable=False),
        sa.Column("comment", sa.String(500)),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("source_hash", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount > 0", name="transactions_amount_positive"),
    )
    op.create_index("ix_transactions_user_date", "transactions", ["user_id", "occurred_at"])
    op.create_index("ix_transactions_user_type", "transactions", ["user_id", "operation_type"])
    op.create_index("ix_transactions_user_category", "transactions", ["user_id", "category_id"])
    op.create_index("ix_transactions_user_source_hash", "transactions", ["user_id", "source_hash"])
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("candidates_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_import_jobs_user_created", "import_jobs", ["user_id", "created_at"])
    op.create_index("ix_import_jobs_user_status", "import_jobs", ["user_id", "status"])
    op.create_table(
        "import_candidates",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("import_job_id", sa.Uuid(), sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Uuid(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("operation_type", sa.String(16), nullable=False),
        sa.Column("occurred_at", sa.Date(), nullable=False),
        sa.Column("comment", sa.String(500)),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False),
        sa.Column("duplicate_status", sa.String(32), nullable=False),
        sa.Column("duplicate_transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("raw_payload", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_import_candidates_job", "import_candidates", ["import_job_id"])
    op.create_index("ix_import_candidates_user_status", "import_candidates", ["user_id", "status"])
    op.create_table(
        "agent_audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("import_job_id", sa.Uuid(), sa.ForeignKey("import_jobs.id", ondelete="SET NULL")),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("input_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candidates_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    categories = sa.table(
        "categories",
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("operation_type_hint", sa.String),
    )
    op.bulk_insert(
        categories,
        [
            {"slug": "products", "name": "Продукты", "operation_type_hint": "expense"},
            {"slug": "transport", "name": "Транспорт", "operation_type_hint": "expense"},
            {"slug": "restaurants", "name": "Кафе и рестораны", "operation_type_hint": "expense"},
            {"slug": "entertainment", "name": "Развлечения", "operation_type_hint": "expense"},
            {"slug": "health", "name": "Здоровье", "operation_type_hint": "expense"},
            {"slug": "transfers", "name": "Переводы", "operation_type_hint": None},
            {"slug": "salary", "name": "Зарплата", "operation_type_hint": "income"},
            {"slug": "other", "name": "Другое", "operation_type_hint": None},
        ],
    )


def downgrade() -> None:
    op.drop_table("agent_audit_logs")
    op.drop_table("import_candidates")
    op.drop_table("import_jobs")
    op.drop_table("transactions")
    op.drop_table("categories")
    op.drop_table("users")

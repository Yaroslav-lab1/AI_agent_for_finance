"""add user profile fields

Revision ID: 20260701_0002
Revises: 20260701_0001
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0002"
down_revision: str | None = "20260701_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("display_name", sa.String(120), nullable=True))
    op.execute(
        """
        UPDATE users
        SET
            username = lower(
                substring(
                    regexp_replace(split_part(email, '@', 1), '[^a-zA-Z0-9_]', '_', 'g')
                    || '_' || substring(id::text from 1 for 8)
                    from 1 for 32
                )
            ),
            display_name = split_part(email, '@', 1)
        WHERE username IS NULL OR display_name IS NULL
        """
    )
    op.alter_column("users", "username", nullable=False)
    op.alter_column("users", "display_name", nullable=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "display_name")
    op.drop_column("users", "username")

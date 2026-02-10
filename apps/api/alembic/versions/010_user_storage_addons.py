"""user_storage_addons: 扩容包表，支持有效期

Revision ID: 010
Revises: 009
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_storage_addons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("add_bytes", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_storage_addons_user_id"), "user_storage_addons", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_storage_addons_expires_at"), "user_storage_addons", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_storage_addons_expires_at"), table_name="user_storage_addons")
    op.drop_index(op.f("ix_user_storage_addons_user_id"), table_name="user_storage_addons")
    op.drop_table("user_storage_addons")

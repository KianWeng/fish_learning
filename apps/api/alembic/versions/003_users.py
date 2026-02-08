"""users table for wechat login

Revision ID: 003
Revises: 002
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("openid", sa.String(length=64), nullable=False),
        sa.Column("unionid", sa.String(length=64), nullable=True),
        sa.Column("nickname", sa.String(length=128), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_openid"), "users", ["openid"], unique=True)
    op.create_index(op.f("ix_users_unionid"), "users", ["unionid"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_unionid"), table_name="users")
    op.drop_index(op.f("ix_users_openid"), table_name="users")
    op.drop_table("users")

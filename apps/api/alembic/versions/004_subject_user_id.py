"""add user_id to subjects for multi-user isolation

Revision ID: 004
Revises: 003
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subjects", sa.Column("user_id", sa.Integer(), nullable=True))
    # 已有数据归属到第一个用户（若尚无用户，请先登录一次再执行迁移）
    op.execute(
        "UPDATE subjects SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1) WHERE user_id IS NULL"
    )
    op.create_foreign_key(
        "fk_subjects_user_id_users",
        "subjects",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_subjects_user_id"), "subjects", ["user_id"], unique=False)
    op.alter_column(
        "subjects",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_subjects_user_id"), table_name="subjects")
    op.drop_constraint("fk_subjects_user_id_users", "subjects", type_="foreignkey")
    op.drop_column("subjects", "user_id")

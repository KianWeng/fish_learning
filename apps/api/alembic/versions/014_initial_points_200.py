"""初始积分 200：新用户默认 200 积分，并为当前积分为 0 的老用户补发

Revision ID: 014
Revises: 013
Create Date: 2025-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 将当前积分为 0 的用户设为 200（老用户补发初始积分）
    op.execute(sa.text("UPDATE users SET points = 200 WHERE points = 0"))
    # 新插入用户的默认积分改为 200
    op.alter_column(
        "users",
        "points",
        existing_type=sa.Integer(),
        server_default=sa.text("200"),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "points",
        existing_type=sa.Integer(),
        server_default=sa.text("0"),
    )

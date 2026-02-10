"""user points & points_ad_logs: 用户积分与广告奖励记录（每日限次）

Revision ID: 012
Revises: 011
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("points", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "points_ad_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_points_ad_logs_user_id"), "points_ad_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_points_ad_logs_user_id"), table_name="points_ad_logs")
    op.drop_table("points_ad_logs")
    op.drop_column("users", "points")

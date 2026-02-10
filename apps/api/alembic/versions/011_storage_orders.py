"""storage_orders: 存储扩容订单表，用于微信支付

Revision ID: 011
Revises: 010
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "storage_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("out_trade_no", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("add_bytes", sa.BigInteger(), nullable=False),
        sa.Column("amount_fen", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_storage_orders_out_trade_no"), "storage_orders", ["out_trade_no"], unique=True)
    op.create_index(op.f("ix_storage_orders_user_id"), "storage_orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_storage_orders_status"), "storage_orders", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_storage_orders_status"), table_name="storage_orders")
    op.drop_index(op.f("ix_storage_orders_user_id"), table_name="storage_orders")
    op.drop_index(op.f("ix_storage_orders_out_trade_no"), table_name="storage_orders")
    op.drop_table("storage_orders")

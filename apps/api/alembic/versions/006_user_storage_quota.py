"""user storage quota: storage_limit_bytes, storage_used_bytes

Revision ID: 006
Revises: 005
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_LIMIT = 100 * 1024 * 1024  # 100MB


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("storage_limit_bytes", sa.BigInteger(), nullable=False, server_default=str(DEFAULT_LIMIT)),
    )
    op.add_column(
        "users",
        sa.Column("storage_used_bytes", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "storage_used_bytes")
    op.drop_column("users", "storage_limit_bytes")

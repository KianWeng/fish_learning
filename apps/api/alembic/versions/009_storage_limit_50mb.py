"""初始免费容量改为 50MB（仅改新用户默认值，不影响已有用户）

Revision ID: 009
Revises: 008
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LIMIT_50MB = 50 * 1024 * 1024  # 52428800


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ALTER COLUMN storage_limit_bytes SET DEFAULT " + str(LIMIT_50MB)
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE users ALTER COLUMN storage_limit_bytes SET DEFAULT 104857600"
    )

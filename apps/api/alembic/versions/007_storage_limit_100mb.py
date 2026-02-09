"""ensure storage_limit_bytes default 100MB; fix existing 10MB rows

Revision ID: 007
Revises: 006
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LIMIT_100MB = 100 * 1024 * 1024  # 104857600


def upgrade() -> None:
    # 将当前小于 100MB 的上限统一改为 100MB（含误设为 10MB 的情况）
    op.execute(
        f"UPDATE users SET storage_limit_bytes = {LIMIT_100MB} WHERE storage_limit_bytes < {LIMIT_100MB}"
    )
    # 确保列默认值为 100MB（新用户或后续建表）
    op.execute(
        f"ALTER TABLE users ALTER COLUMN storage_limit_bytes SET DEFAULT {LIMIT_100MB}"
    )


def downgrade() -> None:
    # 不回退数据，仅保留列与默认
    pass

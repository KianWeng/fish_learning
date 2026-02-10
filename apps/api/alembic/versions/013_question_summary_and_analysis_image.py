"""question summary & analysis_image_url: 知识点易错点摘要、解析附图

Revision ID: 013
Revises: 012
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("questions", sa.Column("analysis_image_url", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "analysis_image_url")
    op.drop_column("questions", "summary")

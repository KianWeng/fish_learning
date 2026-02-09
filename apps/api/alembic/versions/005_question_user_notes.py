"""add user_notes to questions for self-analysis

Revision ID: 005
Revises: 004
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("user_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "user_notes")

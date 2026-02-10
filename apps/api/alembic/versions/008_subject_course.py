"""subject course (科目)

Revision ID: 008
Revises: 007
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subjects", sa.Column("course", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_subjects_course"), "subjects", ["course"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_subjects_course"), table_name="subjects")
    op.drop_column("subjects", "course")

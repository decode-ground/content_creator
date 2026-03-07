"""widen videoPrompts.style to TEXT

Revision ID: a1b2c3d4e5f6
Revises: 0cb61fd871b2
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "0cb61fd871b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "videoPrompts",
        "style",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "videoPrompts",
        "style",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=True,
    )

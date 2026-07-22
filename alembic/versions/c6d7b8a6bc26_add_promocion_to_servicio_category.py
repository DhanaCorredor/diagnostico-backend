"""add promocion to servicio category

Revision ID: c6d7b8a6bc26
Revises: 094deee320e5
Create Date: 2026-07-22 19:25:19.532112

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c6d7b8a6bc26'
down_revision: Union[str, Sequence[str], None] = '094deee320e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE serviciocategoria ADD VALUE IF NOT EXISTS 'PROMOCION'")


def downgrade() -> None:
    """No-op: Postgres no permite quitar un valor de un enum sin recrear el tipo."""
    pass

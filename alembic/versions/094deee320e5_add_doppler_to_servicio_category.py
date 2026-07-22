"""add doppler to servicio category

Revision ID: 094deee320e5
Revises: e9e6824997c0
Create Date: 2026-07-22 19:14:48.578398

"""
from typing import Sequence, Union

from alembic import op

revision: str = '094deee320e5'
down_revision: Union[str, Sequence[str], None] = 'e9e6824997c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE serviciocategoria ADD VALUE IF NOT EXISTS 'DOPPLER'")


def downgrade() -> None:
    """No-op: Postgres no permite quitar un valor de un enum sin recrear el tipo."""
    pass

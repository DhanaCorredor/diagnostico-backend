"""prevent overlapping appointments with an exclusion constraint

Revision ID: 3adfaea5a43a
Revises: 32a037c56fb3
Create Date: 2026-07-28 11:15:46.291649

"""
from typing import Sequence, Union

from alembic import op

revision: str = '3adfaea5a43a'
down_revision: Union[str, Sequence[str], None] = '32a037c56fb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT_NAME = "no_overlapping_appointments_per_doctor"


def upgrade() -> None:
    """Prevent, at database level, a doctor from having two overlapping active appointments."""
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        f"""
        ALTER TABLE citas
        ADD CONSTRAINT {CONSTRAINT_NAME}
        EXCLUDE USING gist (
            medico_id WITH =,
            tsrange(starts_at, ends_at, '[)') WITH &&
        )
        WHERE (estado IN ('SCHEDULED', 'CONFIRMED'))
        """
    )


def downgrade() -> None:
    """Drop the constraint; the btree_gist extension is left installed."""
    op.execute(f"ALTER TABLE citas DROP CONSTRAINT {CONSTRAINT_NAME}")

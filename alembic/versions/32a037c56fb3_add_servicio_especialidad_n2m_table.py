"""add servicio_especialidad n2m table

Revision ID: 32a037c56fb3
Revises: c6d7b8a6bc26
Create Date: 2026-07-23 11:38:16.152301

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '32a037c56fb3'
down_revision: Union[str, Sequence[str], None] = 'c6d7b8a6bc26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "servicio_especialidad",
        sa.Column("servicio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("especialidad_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.ForeignKeyConstraint(["especialidad_id"], ["especialidades.id"]),
        sa.PrimaryKeyConstraint("servicio_id", "especialidad_id"),
    )


def downgrade() -> None:
    op.drop_table("servicio_especialidad")

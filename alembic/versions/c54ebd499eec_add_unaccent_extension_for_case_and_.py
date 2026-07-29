"""add unaccent extension for case and accent insensitive checks

Revision ID: c54ebd499eec
Revises: 3adfaea5a43a
Create Date: 2026-07-29 13:11:23.761225

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c54ebd499eec'
down_revision: Union[str, Sequence[str], None] = '3adfaea5a43a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Install unaccent, used to compare names ignoring case and accents."""
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    """Remove the extension; nothing depends on it structurally."""
    op.execute("DROP EXTENSION IF EXISTS unaccent")

"""Add combo_type column to scout_events

Revision ID: 20260602_add_combo_type
Revises: 20260601_add_reception_layout
Create Date: 2026-06-02 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260602_add_combo_type"
down_revision = "20260601_add_reception_layout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("scout_events")]
    if "combo_type" not in columns:
        op.add_column("scout_events", sa.Column("combo_type", sa.String(length=30), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("scout_events")]
    if "combo_type" in columns:
        op.drop_column("scout_events", "combo_type")

"""Add game_method column to Match table

Revision ID: 20260509_add_game_method
Revises: 20260508_add_status_match_test
Create Date: 2024-05-09 11:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy import inspect, text

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260509_add_game_method"
down_revision = "20260508_add_status_match_test"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Aggiungi colonna game_method a Match (se non esiste già)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("matches")]

    if "game_method" not in columns:
        op.add_column(
            "matches",
            sa.Column(
                "game_method", sa.String(10), nullable=False, server_default="P-S-C"
            ),
        )


def downgrade() -> None:
    # Rimuovi colonna game_method da Match
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("matches")]

    if "game_method" in columns:
        op.drop_column("matches", "game_method")

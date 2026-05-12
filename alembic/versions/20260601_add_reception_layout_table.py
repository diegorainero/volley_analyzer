"""Add table for manual reception layouts by match/set/team

Revision ID: 20260601_add_reception_layout
Revises: 20260509_add_game_method
Create Date: 2026-06-01 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260601_add_reception_layout"
down_revision = "20260509_add_game_method"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "match_set_reception_layouts" not in inspector.get_table_names():
        op.create_table(
            "match_set_reception_layouts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("match_id", sa.Integer(), nullable=False),
            sa.Column("set_number", sa.Integer(), nullable=False),
            sa.Column("team_side", sa.String(length=10), nullable=False),
            sa.Column("positions_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "match_id",
                "set_number",
                "team_side",
                name="uq_match_set_reception_layout",
            ),
        )
        op.create_index(
            "ix_match_set_reception_layouts_match_id",
            "match_set_reception_layouts",
            ["match_id"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "match_set_reception_layouts" in inspector.get_table_names():
        indexes = {
            i.get("name") for i in inspector.get_indexes("match_set_reception_layouts")
        }
        if "ix_match_set_reception_layouts_match_id" in indexes:
            op.drop_index(
                "ix_match_set_reception_layouts_match_id",
                table_name="match_set_reception_layouts",
            )
        op.drop_table("match_set_reception_layouts")

"""Add status column to Match and populate test teams/players

Revision ID: 20260508_add_status_match_test
Revises: 10e6bcebdb00
Create Date: 2024-05-08 11:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy import inspect, text

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260508_add_status_match_test"
down_revision = "10e6bcebdb00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Aggiungi colonne status e updated_at a Match (se non esistono già)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("matches")]

    if "status" not in columns:
        op.add_column(
            "matches",
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        )

    if "updated_at" not in columns:
        op.add_column(
            "matches",
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    # Inserisci le squadre di test
    op.execute(
        text("""
            INSERT INTO teams (name, short_name, category, venue, created_at)
            VALUES
                ('Attacco', 'ATT', 'Test', 'Palazzetto', datetime('now')),
                ('Cihsosla Volley', 'CIS', 'Test', 'Palazzetto', datetime('now'))
        """)
    )

    # Ottieni gli ID delle squadre appena inserite
    team_ids_result = (
        op.get_bind()
        .execute(
            text(
                "SELECT id FROM teams WHERE name IN ('Attacco', 'Cihsosla Volley') ORDER BY id"
            )
        )
        .fetchall()
    )

    if len(team_ids_result) == 2:
        attacco_id, cihsosla_id = team_ids_result[0][0], team_ids_result[1][0]

        # Giocatori per Attacco
        attacco_players = [
            (1, "Marco", "Rossi", "Palleggiatore", False, False),
            (2, "Andrea", "Bianchi", "Schiacciatore", False, False),
            (3, "Luca", "Verdi", "Centrale", False, False),
            (4, "Paolo", "Gialli", "Laterale", False, False),
            (5, "Roberto", "Neri", "Schiacciatore", False, False),
            (6, "Francesco", "Rosa", "Centrale", False, False),
            (7, "Giuseppe", "Arancione", "Opposto", False, False),
            (8, "Stefano", "Blu", "Palleggiatore", False, False),
            (9, "Antonio", "Viola", "Schiacciatore", False, False),
            (10, "Giovanni", "Celeste", "Centrale", False, False),
            (11, "Pietro", "Marrone", "Laterale", False, False),
            (12, "Vittorio", "Grigio", "Opposto", False, False),
            (13, "Carlo", "Magenta", "Libero", True, False),
            (14, "Massimo", "Turchese", "Libero", True, False),
        ]

        # Giocatori per Cihsosla Volley
        cihsosla_players = [
            (10, "Davide", "Verde", "Palleggiatore", False, False),
            (11, "Simone", "Azzurro", "Schiacciatore", False, False),
            (12, "Matteo", "Rosa", "Centrale", False, False),
            (13, "Fabio", "Giallo", "Laterale", False, False),
            (14, "Alessio", "Nero", "Schiacciatore", False, False),
            (15, "Riccardo", "Bianco", "Centrale", False, False),
            (16, "Lorenzo", "Rosso", "Opposto", False, False),
            (17, "Davide", "Arancio", "Palleggiatore", False, False),
            (18, "Nicola", "Marrone", "Schiacciatore", False, False),
            (19, "Tommaso", "Grigio", "Centrale", False, False),
            (20, "Christian", "Viola", "Laterale", False, False),
            (21, "Michele", "Celeste", "Opposto", False, False),
            (22, "Alex", "Lime", "Libero", True, False),
            (23, "Stefano", "Navy", "Libero", True, False),
        ]

        # Inserisci giocatori Attacco
        for number, first_name, last_name, role, is_libero, captain in attacco_players:
            op.execute(
                text(
                    """
                    INSERT INTO players (team_id, number, first_name, last_name, role, is_libero, captain)
                    VALUES (:team_id, :number, :first_name, :last_name, :role, :is_libero, :captain)
                """
                ).bindparams(
                    team_id=attacco_id,
                    number=number,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    is_libero=int(is_libero),
                    captain=int(captain),
                )
            )

        # Inserisci giocatori Cihsosla
        for number, first_name, last_name, role, is_libero, captain in cihsosla_players:
            op.execute(
                text(
                    """
                    INSERT INTO players (team_id, number, first_name, last_name, role, is_libero, captain)
                    VALUES (:team_id, :number, :first_name, :last_name, :role, :is_libero, :captain)
                """
                ).bindparams(
                    team_id=cihsosla_id,
                    number=number,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    is_libero=int(is_libero),
                    captain=int(captain),
                )
            )


def downgrade() -> None:
    # Rimuovi i giocatori di test
    op.execute(
        text(
            "DELETE FROM players WHERE team_id IN (SELECT id FROM teams WHERE name IN ('Attacco', 'Cihsosla Volley'))"
        )
    )

    # Rimuovi le squadre di test
    op.execute(text("DELETE FROM teams WHERE name IN ('Attacco', 'Cihsosla Volley')"))

    # Rimuovi colonne status e updated_at da Match (se esistono)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("matches")]

    if "status" in columns:
        op.drop_column("matches", "status")
    if "updated_at" in columns:
        op.drop_column("matches", "updated_at")

#!/usr/bin/env python3
"""
Test script per verificare il caricamento di FormationPanel con dati dal database
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Player, Team


def test_database_connection():
    """Testa la connessione al database"""
    print("🔍 Testando connessione al database...")
    try:
        db = DatabaseManager()
        print("✅ Database connesso")
        return db
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        return None


def test_load_teams_and_players(db):
    """Testa il caricamento di squadre e giocatori"""
    print("\n🔍 Testando caricamento squadre e giocatori...")
    try:
        teams = []
        players_by_team = {}

        with db.session_scope() as session:
            teams_data = session.query(Team).all()
            print(f"  📊 Squadre trovate: {len(teams_data)}")

            for team in teams_data:
                teams.append({"id": team.id, "name": team.name})
                print(f"    - {team.name} (ID: {team.id})")

                players_data = session.query(Player).filter_by(team_id=team.id).all()
                print(f"      👥 Giocatori: {len(players_data)}")

                players_by_team[team.id] = [
                    {
                        "id": p.id,
                        "number": p.number,
                        "last_name": p.last_name,
                        "role": p.role,
                    }
                    for p in players_data
                ]

                for player in players_by_team[team.id][:3]:  # Mostra i primi 3
                    print(
                        f"        - {player['number']} {player['last_name']} ({player['role']})"
                    )
                if len(players_by_team[team.id]) > 3:
                    print(f"        ... e altri {len(players_by_team[team.id]) - 3}")

        print(f"\n✅ Dati caricati con successo")
        print(f"  Teams: {len(teams)}")
        print(
            f"  Players by team: {[(t_id, len(p)) for t_id, p in players_by_team.items()]}"
        )

        return teams, players_by_team

    except Exception as e:
        print(f"❌ Errore nel caricamento: {e}")
        import traceback

        traceback.print_exc()
        return None, None


def test_formation_panel_initialization(teams, players_by_team):
    """Testa l'inizializzazione di FormationPanel"""
    print("\n🔍 Testando inizializzazione FormationPanel...")
    try:
        from PyQt6.QtWidgets import QApplication

        from volleyball_scout.ui.formation_panel import FormationPanel

        # Crea QApplication se non esiste
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()

        # Testa con dati
        if teams:
            formation_panel = FormationPanel(teams, players_by_team)
            print("✅ FormationPanel creato con successo")
            print(f"  Teams nel panel: {len(formation_panel.teams)}")
            print(f"  Team widgets: {len(formation_panel.team_widgets)}")
            return True
        else:
            print(
                "⚠️  Nessuna squadra disponibile, non è possibile testare FormationPanel"
            )
            return False

    except Exception as e:
        print(f"❌ Errore nell'inizializzazione: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST FORMATION SETUP")
    print("=" * 60)

    # Test 1: Database connection
    db = test_database_connection()
    if not db:
        sys.exit(1)

    # Test 2: Load data
    teams, players_by_team = test_load_teams_and_players(db)

    # Test 3: FormationPanel initialization
    if teams and players_by_team:
        test_formation_panel_initialization(teams, players_by_team)

    print("\n" + "=" * 60)
    print("✅ Test completato")
    print("=" * 60)

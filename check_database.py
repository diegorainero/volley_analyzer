#!/usr/bin/env python3
"""
Script per verificare i dati nel database e mostrare le squadre e i giocatori.
Versione semplice senza dipendenze extra.
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Match, Player, Team


def print_section(title):
    """Stampa un titolo sezione formattato."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_database():
    """Verifica il database e mostra i dati."""

    # Connetti al database
    try:
        db = DatabaseManager()
        print("✅ Connessione al database riuscita!")
        db_info = db.get_db_info()
        print(f"   Database: {db_info['type']} ({db_info['url_safe']})")
        print(f"   Connesso: {db_info['connected']}")
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return

    # Recupera i dati
    try:
        session = db.get_session()

        # Teams
        teams = session.query(Team).all()
        print_section(f"📊 SQUADRE ({len(teams)})")

        if not teams:
            print("   Nessuna squadra nel database")
        else:
            print(
                f"\n{'ID':<5} {'Nome':<30} {'Categoria':<20} {'Impianto':<20} {'Giocatori':<10}"
            )
            print("-" * 85)
            for team in teams:
                player_count = session.query(Player).filter_by(team_id=team.id).count()
                print(
                    f"{team.id:<5} {team.name:<30} {(team.category or '-'):<20} {(team.venue or '-'):<20} {player_count:<10}"
                )

        # Players per team
        print_section("👥 GIOCATORI PER SQUADRA")

        if not teams:
            print("   Nessuna squadra disponibile")
        else:
            for team in teams:
                players = session.query(Player).filter_by(team_id=team.id).all()

                print(f"\n🔹 {team.name} ({len(players)} giocatori)")

                if not players:
                    print("   Nessun giocatore")
                else:
                    print(
                        f"\n  {'#':<5} {'Nome':<20} {'Cognome':<20} {'Ruolo':<20} {'Libero':<10} {'Capitano':<10}"
                    )
                    print("  " + "-" * 80)
                    for player in players:
                        libero = "✓" if player.is_libero else "-"
                        captain = "✓" if player.captain else "-"
                        print(
                            f"  {player.number:<5} {(player.first_name or '-'):<20} {player.last_name:<20} {(player.role or '-'):<20} {libero:<10} {captain:<10}"
                        )

        # Matches
        matches = session.query(Match).all()
        print_section(f"🏐 PARTITE ({len(matches)})")

        if not matches:
            print("   Nessuna partita nel database")
        else:
            print(
                f"\n{'ID':<5} {'Casa':<25} {'Trasferta':<25} {'Data':<20} {'Stato':<10}"
            )
            print("-" * 85)
            for match in matches:
                home = match.home_team.name if match.home_team else "?"
                away = match.away_team.name if match.away_team else "?"
                date_str = match.date.strftime("%Y-%m-%d %H:%M") if match.date else "-"
                status = match.status or "draft"
                print(
                    f"{match.id:<5} {home:<25} {away:<25} {date_str:<20} {status:<10}"
                )

        print_section("✅ VERIFICA COMPLETATA")

        session.close()

    except Exception as e:
        print(f"❌ Errore durante la lettura: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_database()

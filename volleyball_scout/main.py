"""
Volleyball Scout - Main Entry Point
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Crea cartella log se non esiste (PRIMA del logging)
log_dir = Path.home() / ".volleyball_scout"
log_dir.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "scout.log", mode="a", encoding="utf-8"),
    ],
)

try:
    from core.database import get_db
    from core.sync_engine import SyncEngine
except ImportError as e:
    print(f"❌ Errore import: {e}")
    print(
        "   Assicurati di avviare da: cd volley_analizer && python3 volleyball_scout/main.py"
    )
    sys.exit(1)


def main():
    """Avvia l'applicazione Volleyball Scout."""
    print("🏐 Volleyball Scout v0.1 - avvio...")

    # Init DB
    db = get_db()
    info = db.get_db_info()
    print(f"📦 Database: {info['type']} | Connected: {info['connected']}")
    print(f"   URL: {info['url_safe']}")

    # Init Sync Engine
    sync = SyncEngine()
    print("🎬 Sync engine: OK")

    # TODO: avvia UI PyQt6
    print("\n⚠️  UI non ancora collegata - esegui: python ui/main_window.py")
    print("\nPer ora usa la CLI di test:")
    _demo_cli(db, sync)


def _demo_cli(db, sync):
    """Mini demo CLI per testare senza UI"""
    from datetime import datetime

    # Reload sys.path if needed
    if str(Path(__file__).parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).parent))

    from core.models import Match, Player, ScoutEvent, Team

    with db.session_scope() as session:
        # Crea squadre demo se non esistono
        home = session.query(Team).filter_by(name="Cuneo Volley").first()
        if not home:
            home = Team(name="Cuneo Volley", short_name="CUN", category="Serie A2")
            away = Team(name="Modena Volley", short_name="MOD", category="Serie A2")
            session.add_all([home, away])
            session.flush()

            # Giocatori
            for num, nome in [
                (1, "Rossi"),
                (5, "Ferrari"),
                (9, "Bianchi"),
                (11, "Conti"),
                (14, "Ricci"),
                (3, "Libero"),
            ]:
                session.add(
                    Player(
                        team_id=home.id,
                        number=num,
                        last_name=nome,
                        is_libero=(num == 3),
                    )
                )
            for num, nome in [
                (2, "Verdi"),
                (6, "Gialli"),
                (10, "Neri"),
                (12, "Blu"),
                (15, "Rosa"),
            ]:
                session.add(Player(team_id=away.id, number=num, last_name=nome))

            # Partita demo
            match = Match(
                home_team_id=home.id,
                away_team_id=away.id,
                date=datetime.now(),
                venue="PalaCuneo",
                competition="Serie A2",
                video_path="/tmp/demo_match.mp4",
                video_offset=12.5,
            )
            session.add(match)
            session.flush()
            print(f"\n✅ Demo data creata: {match}")
        else:
            print(f"\n✅ Database già popolato: {home.name}")


if __name__ == "__main__":
    # Crea cartella log se non esiste
    log_dir = Path.home() / ".volleyball_scout"
    log_dir.mkdir(parents=True, exist_ok=True)
    main()

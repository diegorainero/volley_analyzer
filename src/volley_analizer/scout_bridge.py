from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScoutModules:
    get_db: object
    Team: object
    Player: object
    Match: object
    MatchSet: object
    ScoutEvent: object
    StatsEngine: object
    SyncEngine: object
    DataVolleyExporter: object


def get_scout_modules() -> ScoutModules:
    """Rende disponibili i moduli di volleyball_scout dentro volley_analizer.

    volleyball_scout usa import assoluti tipo `from core...`; per questo aggiungiamo
    la root `volleyball_scout/` al sys.path in modo esplicito.
    """
    project_root = Path(__file__).resolve().parents[2]
    scout_root = project_root / "volleyball_scout"
    if not scout_root.exists():
        raise FileNotFoundError(f"Cartella volleyball_scout non trovata: {scout_root}")

    scout_root_str = str(scout_root)
    if scout_root_str not in sys.path:
        sys.path.insert(0, scout_root_str)

    from core.database import get_db  # type: ignore
    from core.models import Match, MatchSet, Player, ScoutEvent, Team  # type: ignore
    from core.stats_engine import StatsEngine  # type: ignore
    from core.sync_engine import SyncEngine  # type: ignore
    from exporters.datavolley import DataVolleyExporter  # type: ignore

    return ScoutModules(
        get_db=get_db,
        Team=Team,
        Player=Player,
        Match=Match,
        MatchSet=MatchSet,
        ScoutEvent=ScoutEvent,
        StatsEngine=StatsEngine,
        SyncEngine=SyncEngine,
        DataVolleyExporter=DataVolleyExporter,
    )

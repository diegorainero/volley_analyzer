"""
Volleyball Scout - DataVolley Exporter
Genera file .dvw compatibile con DataVolley 4 / DataProject
Formato documentato: DataProject DVW specification
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import TextIO

from sqlalchemy.orm import Session

from volleyball_scout.core.models import Match, MatchSet, Player, ScoutEvent, Team

logger = logging.getLogger(__name__)


class DataVolleyExporter:
    """
    Esporta una partita nel formato .dvw (DataVolley 4)

    Struttura del file .dvw:
    [3SCOUT]         - header versione
    [3PLAYERS-H]     - roster squadra casa
    [3PLAYERS-V]     - roster squadra ospite
    [3SETS]          - punteggi set
    [3SCOUT]         - eventi di scouting (corpo principale)
    """

    DVW_VERSION = "4"
    DVW_ENCODING = "utf-8"

    def __init__(self, session: Session):
        self.session = session

    # ──────────────────────────────────
    #  Entry point pubblico
    # ──────────────────────────────────

    def export(self, match_id: int, output_path: str | Path) -> Path:
        """Esporta la partita match_id nel file output_path"""
        output_path = Path(output_path)
        match = self.session.get(Match, match_id)
        if not match:
            raise ValueError(f"Match {match_id} non trovato")

        events = (
            self.session.query(ScoutEvent)
            .filter(ScoutEvent.match_id == match_id)
            .order_by(ScoutEvent.id)
            .all()
        )

        sets = (
            self.session.query(MatchSet)
            .filter(MatchSet.match_id == match_id)
            .order_by(MatchSet.set_number)
            .all()
        )

        with open(output_path, "w", encoding=self.DVW_ENCODING, newline="\r\n") as f:
            self._write_header(f, match)
            self._write_players(f, match.home_team, "H")
            self._write_players(f, match.away_team, "V")
            self._write_sets(f, sets)
            self._write_scout_section(f, events)

        logger.info("✅ Export DVW: %s (%d eventi)", output_path, len(events))
        return output_path

    # ──────────────────────────────────
    #  Sezioni del file
    # ──────────────────────────────────

    def _write_header(self, f: TextIO, match: Match):
        f.write("[3SCOUT]\n")
        f.write(f"GAME DATE:{match.date:%d/%m/%Y}\n")
        f.write(f"GAME TIME:{match.date:%H:%M}\n")
        f.write(f"SEASON:{match.date.year}/{match.date.year + 1}\n")
        f.write(f"CHAMPIONSHIP:{match.competition or ''}\n")
        f.write(f"LEG:\n")
        f.write(f"VENUE:{match.venue or ''}\n")
        f.write(f"HOME TEAM:{match.home_team.name}\n")
        f.write(f"VISITING TEAM:{match.away_team.name}\n")
        f.write(f"HOME COACH:\n")
        f.write(f"VISITING COACH:\n")
        f.write(f"COMMENTS:{match.notes or ''}\n")
        f.write(f"SCOUT:\n")
        f.write(f"VIDEO:{Path(match.video_path).name if match.video_path else ''}\n")
        # Set scores
        sets = sorted(match.sets, key=lambda s: s.set_number)
        for i, s in enumerate(sets, 1):
            f.write(f"SET {i}:{s.score_home}-{s.score_away}\n")
        f.write("\n")

    def _write_players(self, f: TextIO, team: Team, side: str):
        f.write(f"[3PLAYERS-{side}]\n")
        players = sorted(team.players, key=lambda p: p.number)
        for p in players:
            libero_flag = "*" if p.is_libero else ""
            f.write(
                f"{p.number};{p.last_name};{p.first_name or ''};{p.role or ''};{libero_flag}\n"
            )
        f.write("\n")

    def _write_sets(self, f: TextIO, sets: list[MatchSet]):
        f.write("[3SETS]\n")
        for s in sets:
            duration = s.duration or 0
            minutes = duration // 60
            seconds = duration % 60
            f.write(
                f"{s.set_number};{s.score_home};{s.score_away};{minutes:02d}:{seconds:02d}\n"
            )
        f.write("\n")

    def _write_scout_section(self, f: TextIO, events: list[ScoutEvent]):
        f.write("[3SCOUT]\n")
        for ev in events:
            line = self._event_to_dvw_line(ev)
            f.write(line + "\n")
        f.write("\n")

    # ──────────────────────────────────
    #  Formato riga evento DataVolley
    # ──────────────────────────────────

    def _event_to_dvw_line(self, ev: ScoutEvent) -> str:
        """
        Formato DVW riga scouting:
        *aNN SS EE ZZ CC II VV TT score-h score-v video_time

        Campi:
        a    = side (a=home, b=away)
        NN   = numero maglia (02)
        SS   = skill code (A/B/D/E/F/R/S)
        EE   = evaluation code (#/+/!/−/=//)
        ZZ   = zona partenza
        CC   = codice combinazione
        II   = codice alzata
        VV   = zona fine
        TT   = codice speciale
        """
        side = ev.team_side or "a"
        number = f"{ev.player.number:02d}" if ev.player else "00"
        skill = ev.skill or "-"
        ev_code = ev.evaluation or "-"
        z_start = ev.zone_start or "0"
        z_end = ev.zone_end or "0"
        combo = ev.attack_combo or "--"
        setcode = ev.set_code or "--"
        special = ev.special_code or "--"
        score_h = f"{ev.score_home:02d}"
        score_v = f"{ev.score_away:02d}"

        # Timestamp video in formato mm:ss.ff
        vt = ev.video_timestamp or 0.0
        vm = int(vt) // 60
        vs = int(vt) % 60
        vf = int((vt % 1) * 100)
        vid_str = f"{vm:02d}:{vs:02d}.{vf:02d}"

        return (
            f"*{side}{number}{skill}{ev_code}{z_start}{combo}{setcode}"
            f"{z_end}{special} {score_h}{score_v} {vid_str}"
        )

    # ──────────────────────────────────
    #  Import da .dvw (reverse)
    # ──────────────────────────────────

    def import_dvw(self, dvw_path: str | Path) -> dict:
        """
        Legge un file .dvw esistente e ritorna i dati parsed.
        Utile per importare partite già schedate con DataVolley ufficiale.
        """
        dvw_path = Path(dvw_path)
        result = {
            "header": {},
            "players_home": [],
            "players_away": [],
            "sets": [],
            "events": [],
        }

        with open(dvw_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        section = None
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("[3PLAYERS-H]"):
                section = "players_home"
                continue
            elif line.startswith("[3PLAYERS-V]"):
                section = "players_away"
                continue
            elif line.startswith("[3SETS]"):
                section = "sets"
                continue
            elif line.startswith("[3SCOUT]"):
                section = "scout"
                continue
            elif line.startswith("["):
                section = None
                continue

            if section == "players_home" or section == "players_away":
                parts = line.split(";")
                if len(parts) >= 2:
                    result[section].append(
                        {
                            "number": int(parts[0]) if parts[0].isdigit() else 0,
                            "last_name": parts[1] if len(parts) > 1 else "",
                            "first_name": parts[2] if len(parts) > 2 else "",
                            "role": parts[3] if len(parts) > 3 else "",
                            "is_libero": "*" in (parts[4] if len(parts) > 4 else ""),
                        }
                    )

            elif section == "sets":
                parts = line.split(";")
                if len(parts) >= 3:
                    result["sets"].append(
                        {
                            "set_number": int(parts[0]),
                            "score_home": int(parts[1]),
                            "score_away": int(parts[2]),
                        }
                    )

            elif section == "scout" and line.startswith("*"):
                parsed = self._parse_dvw_line(line)
                if parsed:
                    result["events"].append(parsed)

        return result

    def _parse_dvw_line(self, line: str) -> dict | None:
        """Parsing di una singola riga scouting .dvw"""
        try:
            # *aNNSEZCCIIVTT ssss mm:ss.ff
            m = re.match(
                r"\*([ab])(\d{2})([ABDEFRS\-])([#+!\-=/])(\d)(..)(..)(.)(..)?\s+(\d{2})(\d{2})\s+(\d{2}):(\d{2})\.(\d{2})",
                line,
            )
            if not m:
                return None
            g = m.groups()
            vt = int(g[11]) * 60 + int(g[12]) + int(g[13]) / 100.0
            return {
                "team_side": g[0],
                "player_number": int(g[1]),
                "skill": g[2],
                "evaluation": g[3],
                "zone_start": g[4],
                "attack_combo": g[5],
                "set_code": g[6],
                "zone_end": g[7],
                "special_code": g[8],
                "score_home": int(g[9]),
                "score_away": int(g[10]),
                "video_timestamp": vt,
            }
        except Exception as e:
            logger.debug("Parse line failed '%s': %s", line[:40], e)
            return None

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import TextIO

from sqlalchemy.orm import Session

from volleyball_scout.core.models import Match, MatchSet, Player, ScoutEvent, Team

logger = logging.getLogger(__name__)

SKILL_TO_DV = {
    "S": "SQ",
    "R": "RQ",
    "A": "AH",
    "F": "FU",
    "B": "BH",
    "D": "DH",
    "E": "SE",
}


class DataVolleyExporter:
    def __init__(self, session: Session):
        self.session = session

    def export(self, match_id: int, output_path: str | Path) -> Path:
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

        with open(output_path, "w", encoding="utf-8", newline="\r\n") as f:
            self._write_dvheader(f, match)
            self._write_match(f, match)
            self._write_teams(f, match)
            self._write_set(f, sets)
            self._write_players(f, match.home_team, "H")
            self._write_players(f, match.away_team, "V")
            self._write_video(f, match)
            self._write_scout(f, events, match)

        logger.info("Export DVW: %s (%d eventi)", output_path, len(events))
        return output_path

    def _write_dvheader(self, f: TextIO, match: Match):
        f.write("[3DATAVOLLEYSCOUT]\n")
        f.write("FILEFORMAT: 2.0\n")
        f.write(f"GENERATOR-DAY: {match.date:%d/%m/%Y %H:%M}\n")
        f.write("GENERATOR-IDP: SCOUT\n")
        f.write("GENERATOR-PRG: Volleyball Scout\n")
        f.write("GENERATOR-REL: 1.0\n")
        f.write("GENERATOR-VER: Professional\n")
        f.write("GENERATOR-NAM: \n")
        f.write("LASTCHANGE-DAY: \n")
        f.write("LASTCHANGE-IDP: DVW\n")
        f.write("LASTCHANGE-PRG: Volleyball Scout\n")
        f.write("LASTCHANGE-REL: 1.0\n")
        f.write("LASTCHANGE-VER: Professional\n")
        f.write("LASTCHANGE-NAM: \n")

    def _write_match(self, f: TextIO, match: Match):
        f.write("[3MATCH]\n")
        home_code = (match.home_team.short_name or match.home_team.name[:3].upper()) if match.home_team else "HOME"
        away_code = (match.away_team.short_name or match.away_team.name[:3].upper()) if match.away_team else "AWAY"
        home_name = match.home_team.name if match.home_team else "Casa"
        away_name = match.away_team.name if match.away_team else "Ospiti"
        f.write(
            f"{match.date:%d/%m/%Y};{match.date:%H.%M.%S};;{match.competition or ''};;;"
            f"5;;1252;1;Z;0;{home_name};{home_code};{away_name};{away_code};\n"
        )

    def _write_teams(self, f: TextIO, match: Match):
        f.write("[3TEAMS]\n")
        if match.home_team:
            code = match.home_team.short_name or match.home_team.name[:3].upper()
            name = match.home_team.name
            f.write(f"{code};{name};;; ;16777215;;;;\n")
        if match.away_team:
            code = match.away_team.short_name or match.away_team.name[:3].upper()
            name = match.away_team.name
            f.write(f"{code};{name};;; ;16777215;;;;\n")

    def _write_set(self, f: TextIO, sets: list[MatchSet]):
        f.write("[3SET]\n")
        for s in sorted(sets, key=lambda x: x.set_number):
            scores = [f"{s.score_home} -{s.score_away}"]
            f.write(f"True;{' ;'.join(scores * 5)};\n")
        for _ in range(5 - len(sets)):
            f.write("False;;;;;;\n")

    def _write_players(self, f: TextIO, team: Team, side: str):
        f.write(f"[3PLAYERS-{side}]\n")
        players = sorted(team.players, key=lambda p: p.number)
        for p in players:
            libero_flag = "L" if p.is_libero else ""
            f.write(
                f"0;{p.number};{p.number};;;;;"
                f"{p.last_name[:7]};{p.last_name};{p.first_name or ''};;;0;{libero_flag};;\n"
            )

    def _write_video(self, f: TextIO, match: Match):
        f.write("[3VIDEO]\n")
        if match.video_path:
            f.write(f"Camera0={match.video_path}\n")
        f.write("\n")

    def _write_scout(self, f: TextIO, events: list[ScoutEvent], match: Match):
        f.write("[3SCOUT]\n")
        current_set = 0
        for ev in events:
            if ev.set_id:
                ms = self.session.get(MatchSet, ev.set_id)
                set_num = ms.set_number if ms else 1
            else:
                set_num = 1

            if set_num != current_set:
                if current_set > 0:
                    pass
                current_set = set_num

            line = self._event_to_line(ev, set_num)
            if line:
                f.write(line + "\n")

    def _event_to_line(self, ev: ScoutEvent, set_num: int) -> str | None:
        skill_dv = SKILL_TO_DV.get(ev.skill, ev.skill or "??")
        number = f"{ev.player.number:02d}" if ev.player else "00"
        eval_code = ev.evaluation or "-"
        team_prefix = "*" if ev.team_side == "a" else "a"
        combo = ev.attack_combo or ""
        score_h = ev.score_home or 0
        score_a = ev.score_away or 0
        rally = ev.rally_number or 0
        ts_str = ""
        if ev.video_timestamp is not None:
            vm = int(ev.video_timestamp) // 60
            vs = int(ev.video_timestamp) % 60
            ts_str = f"{vm:02d}:{vs:02d}"

        zone_suffix = ""
        if ev.zone_start and ev.zone_end:
            zone_suffix = f"{ev.zone_start}{ev.zone_end}"
        elif ev.zone_start:
            zone_suffix = f"{ev.zone_start}"

        code = f"{team_prefix}{number}{skill_dv}{eval_code}"
        if zone_suffix:
            code += f"~{zone_suffix}"
        if combo:
            code += f"~{combo}"

        return (
            f"{code};;;;;;;{ts_str};{set_num};1;1;{score_h};{rally};;"
            f"0;0;0;0;0;0;0;0;0;0;0;0;"
        )

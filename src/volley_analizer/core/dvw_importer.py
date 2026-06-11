from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SKILL_MAP = {
    "SQ": "S", "SM": "S", "SF": "S", "SH": "S",
    "RQ": "R", "RM": "R",
    "SE": "E", "EH": "E", "EU": "E", "EQ": "E", "EO": "E", "EM": "E", "EP": "E",
    "AH": "A", "AU": "A", "AM": "A", "AQ": "A", "AO": "A", "TT": "A",
    "FU": "F", "FH": "F",
    "BH": "B", "BM": "B", "BO": "B", "BD": "B",
    "DH": "D", "BU": "D",
}

EVAL_MAP = {"#": "#", "+": "+", "!": "!", "-": "-", "=": "=", "/": "/"}


@dataclass
class DvwMatch:
    file_format: str = "2.0"
    date: datetime | None = None
    competition: str = ""
    venue: str = ""
    home_team_code: str = ""
    home_team_name: str = ""
    away_team_code: str = ""
    away_team_name: str = ""
    referee: str = ""
    video_path: str = ""


@dataclass
class DvwPlayer:
    number: int
    shirt: int = 0
    last_name: str = ""
    first_name: str = ""
    role: str = ""
    is_libero: bool = False
    team_side: str = ""


@dataclass
class DvwSet:
    set_number: int = 0
    score_home: int = 0
    score_away: int = 0
    home_lineup: dict[str, str] = field(default_factory=dict)
    away_lineup: dict[str, str] = field(default_factory=dict)


@dataclass
class DvwAction:
    team_side: str = "home"
    player_number: int | None = None
    skill: str = ""
    skill_raw: str = ""
    evaluation: str | None = None
    zone_start: str | None = None
    zone_end: str | None = None
    attack_combo: str | None = None
    set_code: str | None = None
    set_number: int = 1
    rotation: int = 1
    rally: int = 0
    timestamp: float | None = None
    score_home: int = 0
    score_away: int = 0
    kind: str = "action"
    home_lineup: dict[str, str] = field(default_factory=dict)
    away_lineup: dict[str, str] = field(default_factory=dict)


@dataclass
class DvwParseResult:
    match: DvwMatch = field(default_factory=DvwMatch)
    home_players: list[DvwPlayer] = field(default_factory=list)
    away_players: list[DvwPlayer] = field(default_factory=list)
    sets: list[DvwSet] = field(default_factory=list)
    actions: list[DvwAction] = field(default_factory=list)
    attack_combos: list[dict] = field(default_factory=list)
    setter_calls: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def detect_format(lines: list[str]) -> str:
    for line in lines:
        if "Click&Scout" in line:
            return "click_and_scout"
        if "Data Volley" in line or "DATAVOLLEYSCOUT" in line:
            pass
    for line in lines:
        stripped = line.strip().lstrip("*aAbB")
        if re.match(r"\d{1,2}[A-Z]{2}[#+!\-=/]", stripped):
            rest = stripped[4:]
            if "~" in rest:
                parts = rest.split(";")
                if len(parts) >= 2:
                    eval_part = parts[0]
                    if eval_part.count("~") >= 2:
                        return "full_datavolley"
    return "click_and_scout"


class DvwImporter:
    def __init__(self):
        self.ts_reference: float = 0.0

    def parse_file(self, path: str | Path) -> DvwParseResult:
        path = Path(path)
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        sections = self._split_sections(lines)
        fmt = detect_format(lines)
        logger.info("Rilevato formato DVW: %s", fmt)
        result = DvwParseResult()
        self._parse_header(sections, result)
        self._parse_teams(sections, result)
        self._parse_players(sections, "H", result, "home")
        self._parse_players(sections, "V", result, "away")
        self._parse_sets(sections, result)
        self._parse_video(sections, result)
        self._parse_attack_combos(sections, result)
        self._parse_setter_calls(sections, result)
        self._parse_scout(sections, result, fmt)
        return result

    def parse_file_to_dict(self, path: str | Path) -> dict[str, Any]:
        result = self.parse_file(path)
        return {
            "match": {
                "date": result.match.date.isoformat() if result.match.date else None,
                "competition": result.match.competition,
                "venue": result.match.venue,
                "home_team": {"code": result.match.home_team_code, "name": result.match.home_team_name},
                "away_team": {"code": result.match.away_team_code, "name": result.match.away_team_name},
                "video_path": result.match.video_path,
            },
            "home_players": [
                {"number": p.number, "last_name": p.last_name, "first_name": p.first_name,
                 "role": p.role, "is_libero": p.is_libero}
                for p in result.home_players
            ],
            "away_players": [
                {"number": p.number, "last_name": p.last_name, "first_name": p.first_name,
                 "role": p.role, "is_libero": p.is_libero}
                for p in result.away_players
            ],
            "sets": [
                {"set_number": s.set_number, "score_home": s.score_home, "score_away": s.score_away}
                for s in result.sets
            ],
            "actions": [
                {
                    "kind": a.kind, "team_side": a.team_side, "player_number": a.player_number,
                    "skill": a.skill, "skill_raw": a.skill_raw, "evaluation": a.evaluation,
                    "zone_start": a.zone_start, "zone_end": a.zone_end,
                    "attack_combo": a.attack_combo, "set_number": a.set_number,
                    "rotation": a.rotation, "rally": a.rally,
                    "score_home": a.score_home, "score_away": a.score_away,
                    "home_lineup": a.home_lineup, "away_lineup": a.away_lineup,
                }
                for a in result.actions
            ],
        }

    def _split_sections(self, lines: list[str]) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                name = stripped.strip("[]")
                current = name
                sections[name] = []
            elif current is not None and stripped:
                sections[current].append(stripped)
        return sections

    def _parse_header(self, sections: dict, result: DvwParseResult):
        match_lines = sections.get("3MATCH", [])
        if match_lines:
            parts = match_lines[0].split(";")
            if len(parts) >= 2:
                try:
                    date_str = parts[0].strip()
                    time_str = parts[1].strip()
                    dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H.%M.%S")
                    result.match.date = dt
                except ValueError:
                    try:
                        dt = datetime.strptime(f"{parts[0].strip()} {parts[1].strip()}",
                                                "%d/%m/%Y %H.%M.%S")
                        result.match.date = dt
                    except ValueError:
                        pass
                if len(parts) >= 3:
                    result.match.competition = parts[2].strip()
        more_lines = sections.get("3MORE", [])
        if more_lines:
            parts = more_lines[0].split(";")
            if len(parts) >= 2:
                result.match.venue = parts[1].strip()

    def _parse_teams(self, sections: dict, result: DvwParseResult):
        teams = sections.get("3TEAMS", [])
        if teams:
            parts = teams[0].split(";")
            if len(parts) >= 2:
                result.match.home_team_code = parts[0].strip()
                result.match.home_team_name = self._clean_name(parts[1])
            if len(parts) >= 3:
                pass
        if len(teams) > 1:
            parts = teams[1].split(";")
            if len(parts) >= 2:
                result.match.away_team_code = parts[0].strip()
                result.match.away_team_name = self._clean_name(parts[1])

    def _clean_name(self, raw: str) -> str:
        raw = raw.strip()
        try:
            if "\\x" in raw:
                hex_match = re.search(r'\\x([0-9A-Fa-f]+)', raw)
                if hex_match:
                    hex_str = hex_match.group(1)
                    decoded = bytes.fromhex(hex_str).decode("utf-16-be", errors="replace")
                    raw = raw.replace(hex_match.group(0), decoded)
            raw = raw.replace("\\x00", "").replace("\x00", "")
            raw = raw.strip()
        except Exception:
            pass
        return raw

    def _parse_players(self, sections: dict, side: str, result: DvwParseResult, team_side: str):
        key = f"3PLAYERS-{side}"
        players_list = []
        for line in sections.get(key, []):
            parts = line.split(";")
            if len(parts) < 8:
                continue
            try:
                number = int(parts[1])
            except (ValueError, IndexError):
                continue
            if number == 0:
                continue
            p = DvwPlayer(
                number=number,
                last_name=self._clean_name(parts[8] if len(parts) > 8 else ""),
                first_name=self._clean_name(parts[9] if len(parts) > 9 else ""),
                role="",
                is_libero="L" in (parts[11] if len(parts) > 11 else ""),
                team_side=team_side,
            )
            if len(parts) > 2 and parts[2].lstrip("0").isdigit():
                p.shirt = int(parts[2])
            else:
                p.shirt = number
            players_list.append(p)
        if team_side == "home":
            result.home_players = players_list
        else:
            result.away_players = players_list

    def _parse_sets(self, sections: dict, result: DvwParseResult):
        for line in sections.get("3SET", []):
            parts = line.split(";")
            if len(parts) >= 6 and parts[0].strip().lower() == "true":
                final_score = None
                for i in range(1, len(parts)):
                    score_part = parts[i].strip()
                    if not score_part or score_part in ("0 -0", "0-0"):
                        continue
                    try:
                        if "-" in score_part:
                            h, a = score_part.split("-", 1)
                            final_score = [int(h.strip()), int(a.strip())]
                    except (ValueError, IndexError):
                        continue
                if final_score:
                    s = DvwSet(
                        set_number=len(result.sets) + 1,
                        score_home=final_score[0],
                        score_away=final_score[1],
                    )
                    result.sets.append(s)

    def _parse_video(self, sections: dict, result: DvwParseResult):
        for line in sections.get("3VIDEO", []):
            if line.startswith("Camera0="):
                result.match.video_path = line.split("=", 1)[1].strip()
                break

    def _parse_attack_combos(self, sections: dict, result: DvwParseResult):
        for line in sections.get("3ATTACKCOMBINATION", []):
            parts = line.split(";")
            if len(parts) >= 3:
                result.attack_combos.append({
                    "code": parts[0].strip(),
                    "category": parts[1].strip(),
                    "side": parts[2].strip(),
                    "type": parts[3].strip() if len(parts) > 3 else "",
                    "description": parts[4].strip() if len(parts) > 4 else "",
                })

    def _parse_setter_calls(self, sections: dict, result: DvwParseResult):
        for line in sections.get("3SETTERCALL", []):
            parts = line.split(";")
            if len(parts) >= 2:
                result.setter_calls.append({
                    "code": parts[0].strip(),
                    "label": parts[1].strip(),
                    "description": parts[2].strip() if len(parts) > 2 else "",
                })

    def _parse_scout(self, sections: dict, result: DvwParseResult, fmt: str):
        raw_lines = sections.get("3SCOUT", [])
        actions, sets_data = self._parse_scout_lines(raw_lines, fmt)
        result.actions = actions
        for action in actions:
            if action.kind == "lineup" and 1 <= action.set_number <= len(result.sets):
                s = result.sets[action.set_number - 1]
                if action.team_side == "home":
                    s.home_lineup = action.home_lineup
                else:
                    s.away_lineup = action.away_lineup

    def _parse_scout_lines(self, raw_lines: list[str], fmt: str) -> tuple[list[DvwAction], dict]:
        actions: list[DvwAction] = []
        sets_info: dict[int, dict] = {}
        current_set = 1
        rotation_home = 1
        rotation_away = 1
        score_home = 0
        score_away = 0
        rally = 0
        last_lineup_home: dict[str, str] = {}
        last_lineup_away: dict[str, str] = {}

        for raw in raw_lines:
            if raw.startswith("**") and "set" not in raw:
                continue
            if raw.startswith("**") and "set" in raw:
                m = re.search(r"\*\*(\d)set", raw)
                if m:
                    current_set = int(m.group(1))
                continue

            parts = raw.split(";")
            if len(parts) > 8:
                try:
                    raw_set = int(parts[8].strip())
                    if 1 <= raw_set <= 5 and raw_set != current_set:
                        current_set = raw_set
                except (ValueError, IndexError):
                    pass

            if not raw.startswith(("*", "a", "A", "b", "B")):
                continue

            team_side = "away" if raw.startswith(("a", "b", "A", "B")) else "home"

            raw_rotation = self._extract_raw_rotation(parts)
            if raw_rotation is not None:
                if team_side == "home":
                    rotation_home = raw_rotation
                else:
                    rotation_away = raw_rotation

            action = self._parse_single_line(raw, parts, fmt, current_set,
                                              rotation_home, rotation_away,
                                              score_home, score_away, rally)

            if action is None:
                continue

            if action.kind == "rotation":
                if action.team_side == "home":
                    rotation_home = action.rotation
                else:
                    rotation_away = action.rotation
                continue

            if action.kind == "point":
                if action.score_home is not None:
                    score_home = action.score_home
                    score_away = action.score_away
                continue

            if action.kind in ("player_position",):
                pass

            lineup = self._extract_lineup(parts)
            if lineup:
                last_lineup_home = lineup["home"]
                last_lineup_away = lineup["away"]
                if not any(a.set_number == current_set and a.kind == "lineup" for a in actions):
                    lineup_action_1 = DvwAction(
                        kind="lineup", team_side="home", set_number=current_set,
                        home_lineup=last_lineup_home, away_lineup=last_lineup_away,
                    )
                    actions.append(lineup_action_1)

            if action.kind == "action":
                action.home_lineup = dict(last_lineup_home)
                action.away_lineup = dict(last_lineup_away)
                rally += 1
                action.rally = rally

            actions.append(action)

        return actions, sets_info

    def _parse_single_line(self, raw: str, parts: list[str], fmt: str,
                            current_set: int, rot_h: int, rot_a: int,
                            score_h: int, score_a: int, rally: int) -> DvwAction | None:
        team_side = "away" if raw.startswith(("a", "A")) else "home"
        prefix = raw.lstrip("*aAbB")

        if prefix.startswith("**"):
            return None

        if prefix.startswith("$"):
            return DvwAction(kind="point", team_side=team_side,
                              score_home=score_h, score_away=score_a,
                              set_number=current_set, rotation=rot_h if team_side == "home" else rot_a)

        m_p = re.match(r"P(\d+)", prefix)
        if m_p:
            return DvwAction(kind="player_position", team_side=team_side,
                              player_number=int(m_p.group(1)),
                              set_number=current_set, rotation=rot_h if team_side == "home" else rot_a)

        if prefix.startswith("T"):
            return DvwAction(kind="timeout", team_side=team_side,
                              set_number=current_set, rotation=rot_h if team_side == "home" else rot_a)

        m_sub = re.match(r"c(\d+):(\d+)", prefix)
        if m_sub:
            return DvwAction(kind="substitution", team_side=team_side,
                              player_number=int(m_sub.group(1)),
                              set_number=current_set)

        m_z = re.match(r"z(\d)", prefix)
        if m_z:
            rot = int(m_z.group(1))
            return DvwAction(kind="rotation", team_side=team_side,
                              rotation=rot, set_number=current_set)

        m_point = re.match(r"p(\d+):(\d+)", prefix)

        if m_point or prefix.startswith("p"):
            if m_point:
                return DvwAction(kind="point", team_side=team_side,
                                  score_home=int(m_point.group(1)),
                                  score_away=int(m_point.group(2)),
                                  set_number=current_set, rotation=rot_h if team_side == "home" else rot_a,
                                  timestamp=self._extract_timestamp(parts))
            return DvwAction(kind="point", team_side=team_side,
                              score_home=score_h, score_away=score_a,
                              set_number=current_set, rotation=rot_h if team_side == "home" else rot_a)

        if fmt == "full_datavolley":
            action = self._parse_full_format(prefix, team_side, current_set,
                                              rot_h, rot_a, score_h, score_a, parts)
        else:
            action = self._parse_simple_format(prefix, team_side, current_set,
                                               rot_h, rot_a, score_h, score_a, parts)

        if action:
            action.timestamp = self._extract_timestamp(parts)
            return action

        m_action = re.match(r"(\d{1,2})([A-Z]{2})([#+!\-=/]?)", prefix)
        if m_action:
            action = DvwAction(
                kind="action", team_side=team_side,
                player_number=int(m_action.group(1)),
                skill_raw=m_action.group(2),
                skill=SKILL_MAP.get(m_action.group(2), m_action.group(2)),
                evaluation=m_action.group(3) or None,
                set_number=current_set,
                rotation=rot_h if team_side == "home" else rot_a,
                score_home=score_h, score_away=score_a,
            )
            rest = prefix[m_action.end():]
            self._extract_zones_and_combo(rest, action, fmt)
            return action

        return None

    def _parse_simple_format(self, code: str, team_side: str,
                              current_set: int, rot_h: int, rot_a: int,
                              score_h: int, score_a: int, parts: list[str]) -> DvwAction | None:
        m = re.match(r"(\d{1,2})([A-Z]{2})([#+!\-=/]?)", code)
        if not m:
            return None

        action = DvwAction(
            kind="action", team_side=team_side,
            player_number=int(m.group(1)),
            skill_raw=m.group(2),
            skill=SKILL_MAP.get(m.group(2), m.group(2)),
            evaluation=m.group(3) or None,
            set_number=current_set,
            rotation=rot_h if team_side == "home" else rot_a,
            score_home=score_h, score_away=score_a,
        )

        rest = code[m.end():]
        self._extract_zones_and_combo(rest, action, "click_and_scout")
        return action

    def _parse_full_format(self, code: str, team_side: str,
                            current_set: int, rot_h: int, rot_a: int,
                            score_h: int, score_a: int, parts: list[str]) -> DvwAction | None:
        m = re.match(r"(\d{1,2})([A-Z]{2})([#+!\-=/]?)", code)
        if not m:
            m = re.match(r"(\d{1,2})([A-Z]{2})", code)
            if not m:
                return None
            eval_str = None
        else:
            eval_str = m.group(3) or None

        action = DvwAction(
            kind="action", team_side=team_side,
            player_number=int(m.group(1)),
            skill_raw=m.group(2),
            skill=SKILL_MAP.get(m.group(2), m.group(2)),
            evaluation=eval_str,
            set_number=current_set,
            rotation=rot_h if team_side == "home" else rot_a,
            score_home=score_h, score_away=score_a,
        )

        rest = code[m.end():]
        self._extract_zones_and_combo(rest, action, "full_datavolley")
        return action

    def _extract_zones_and_combo(self, rest: str, action: DvwAction, fmt: str):
        if fmt == "full_datavolley":
            self._extract_full_zones(rest, action)
        else:
            self._extract_simple_zones(rest, action)

    def _extract_simple_zones(self, rest: str, action: DvwAction):
        rest = rest.lstrip("~")
        m = re.match(r"(\d)(\d)", rest)
        if m:
            action.zone_start = m.group(1)
            action.zone_end = m.group(2)
            rest = rest[2:]

        combo_end = re.search(r"[;~]", rest)
        combo_raw = rest[:combo_end.start()] if combo_end else rest
        combo_raw = combo_raw.rstrip("~")

        if combo_raw and len(combo_raw) >= 2:
            known_combos = {
                "X1", "X2", "XM", "XG", "XC", "XD", "X7", "XS", "XO", "XF",
                "XP", "XB", "XR", "X9", "XT", "X3", "X4", "XQ", "X5", "X0", "X6", "X8",
                "CD", "CB", "CF", "C5", "C0", "C6", "C8",
                "V5", "V0", "V6", "V8", "VB", "VP", "VR", "V3",
                "P2", "PR", "PP", "P3",
            }
            potential_combo = combo_raw[:2].upper()
            if potential_combo in known_combos:
                action.attack_combo = potential_combo

    def _extract_full_zones(self, rest: str, action: DvwAction):
        segments = rest.split("~")
        segments = [s for s in segments if s]

        known_combos = {
            "X1", "X2", "XM", "XG", "XC", "XD", "X7", "XS", "XO", "XF",
            "XP", "XB", "XR", "X9", "XT", "X3", "X4", "XQ", "X5", "X0", "X6", "X8",
            "CD", "CB", "CF", "C5", "C0", "C6", "C8",
            "V5", "V0", "V6", "V8", "VB", "VP", "VR", "V3",
            "P2", "PR", "PP", "P3",
            "K1", "K2", "K7", "KC", "KM", "KP", "KE", "KF",
        }

        for seg in segments:
            potential = seg[:2].upper()
            if potential in known_combos:
                if action.skill == "A" and not action.attack_combo:
                    action.attack_combo = potential
                elif action.skill_raw in ("EH", "EU", "EQ", "EO", "EM", "EP", "SE"):
                    action.set_code = potential
            zone_match = re.match(r"(\d)(\d)", seg)
            if zone_match:
                if action.skill in ("A", "S"):
                    action.zone_start = zone_match.group(1)
                    action.zone_end = zone_match.group(2)
                elif action.zone_end is None:
                    action.zone_end = zone_match.group(2)

    def _extract_lineup(self, parts: list[str]) -> dict | None:
        if len(parts) < 26:
            return None
        home = {}
        away = {}
        pos_codes = ["P1", "P2", "P3", "P4", "P5", "P6"]
        home_nums = [p.strip() for p in parts[14:20]]
        away_nums = [p.strip() for p in parts[20:26]]
        if any(not n.isdigit() for n in home_nums + away_nums):
            for n in home_nums + away_nums:
                if n and not n.isdigit():
                    return None
        for pos, num in zip(pos_codes, home_nums):
            home[pos] = num
        for pos, num in zip(pos_codes, away_nums):
            away[pos] = num
        return {"home": home, "away": away}

    def _extract_timestamp(self, parts: list[str]) -> float | None:
        if len(parts) > 7:
            ts_str = parts[7].strip()
            try:
                t = datetime.strptime(ts_str, "%H.%M.%S")
                ref = datetime.strptime("00.00.00", "%H.%M.%S")
                abs_seconds = (t - ref).total_seconds()
                if self.ts_reference == 0:
                    self.ts_reference = abs_seconds
                return abs_seconds - self.ts_reference
            except ValueError:
                return None
        return None

    def _extract_raw_rotation(self, parts: list[str]) -> int | None:
        if len(parts) > 9:
            try:
                rot = int(parts[9].strip())
                if 1 <= rot <= 6:
                    return rot
            except (ValueError, IndexError):
                pass
        return None

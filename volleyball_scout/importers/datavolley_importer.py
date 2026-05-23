import logging
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from volleyball_scout.core.models import Match, MatchSet, Player, ScoutEvent, Team

logger = logging.getLogger(__name__)

SKILL_MAP = {
    "SQ": "S", "SH": "S", "SM": "S", "SF": "S",
    "RQ": "R",
    "SE": "E", "EH": "E", "EU": "E", "EQ": "E", "EO": "E", "EM": "E", "EP": "E",
    "AH": "A", "AU": "A", "AM": "A", "AQ": "A", "AO": "A", "TT": "A",
    "FU": "F", "FH": "F",
    "BH": "B", "BM": "B", "BO": "B", "BD": "B",
    "DH": "D",
}

EVAL_MAP = {"#": "#", "+": "+", "!": "!", "-": "-", "=": "=", "/": "/"}


class DataVolleyImporter:
    def __init__(self, session: Session):
        self.session = session
        self.last_video_ts: float = 0.0
        self.current_set = 0
        self.current_rotation_home = 1
        self.current_rotation_away = 1
        self.ts_reference: float = 0.0

    def import_file(self, dvw_path: str | Path) -> dict:
        self._migrate_schema()
        dvw_path = Path(dvw_path)
        with open(dvw_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        sections = self._split_sections(lines)
        match_data = self._parse_header(sections)
        teams_data = self._parse_teams(sections)
        players_home = self._parse_players(sections, "H")
        players_away = self._parse_players(sections, "V")
        set_scores = self._parse_sets(sections)
        video_path = self._parse_video(sections)
        scout_lines = self._parse_scout_lines(sections)
        self._compute_ts_reference(scout_lines)

        home_team = self._get_or_create_team(teams_data["home"])
        away_team = self._get_or_create_team(teams_data["away"])

        match = self._create_match(match_data, home_team, away_team, video_path)
        if match is None:
            self.session.rollback()
            return {"duplicate": True, "home_team": home_team.name, "away_team": away_team.name}
        self._import_players(players_home, home_team, match)
        self._import_players(players_away, away_team, match)
        self._create_sets(match, set_scores)
        self._import_events(match, home_team, away_team, scout_lines, set_scores)

        self.session.commit()
        return {"match_id": match.id, "home_team": home_team.name, "away_team": away_team.name}

    def _compute_ts_reference(self, scout_lines: list[str]):
        for line in scout_lines:
            parts = line.split(";")
            if len(parts) > 7:
                ts_str = parts[7].strip()
                if ts_str and ts_str.replace(".", "").isdigit():
                    try:
                        t = datetime.strptime(ts_str, "%H.%M.%S")
                        ref = datetime.strptime("00.00.00", "%H.%M.%S")
                        self.ts_reference = (t - ref).total_seconds()
                    except ValueError:
                        pass
                    return

    def _split_sections(self, lines: list[str]) -> dict[str, list[str]]:
        sections = {}
        current = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                name = stripped.strip("[]")
                current = []
                sections[name] = current
            elif current is not None and stripped:
                current.append(stripped)
        return sections

    def _parse_header(self, sections: dict) -> dict:
        result = {
            "date": datetime.now(),
            "competition": "",
            "venue": "",
        }
        match_lines = sections.get("3MATCH", [])
        if match_lines:
            parts = match_lines[0].split(";")
            if len(parts) >= 2:
                try:
                    date_str = parts[0].strip()
                    time_str = parts[1].strip()
                    dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H.%M.%S")
                    result["date"] = dt
                except ValueError:
                    pass
        return result

    def _parse_teams(self, sections: dict) -> dict:
        result = {"home": {}, "away": {}}
        teams = sections.get("3TEAMS", [])
        if teams:
            parts = teams[0].split(";")
            if len(parts) >= 2:
                result["home"]["code"] = parts[0].strip()
                result["home"]["name"] = self._decode_hex_name(parts[1].strip())
            if len(parts) >= 3:
                pass
        if len(teams) > 1:
            parts = teams[1].split(";")
            if len(parts) >= 2:
                result["away"]["code"] = parts[0].strip()
                result["away"]["name"] = self._decode_hex_name(parts[1].strip())
        return result

    def _decode_hex_name(self, raw: str) -> str:
        try:
            if raw.startswith("\\x"):
                return bytes.fromhex(raw[2:]).decode("utf-16-be")
            if raw.startswith("\\") and re.match(r"^\\x[0-9A-Fa-f]+", raw):
                hex_part = raw[2:]
                return bytes.fromhex(hex_part).decode("utf-16-be")
        except Exception:
            pass
        return raw

    def _parse_players(self, sections: dict, side: str) -> list[dict]:
        key = f"3PLAYERS-{side}"
        players = []
        for line in sections.get(key, []):
            parts = line.split(";")
            if len(parts) >= 8:
                try:
                    number = int(parts[1])
                except (ValueError, IndexError):
                    number = 0
                if number == 0:
                    continue
                player = {
                    "number": number,
                    "last_name": self._clean_name(parts[8] if len(parts) > 8 else ""),
                    "first_name": self._clean_name(parts[9] if len(parts) > 9 else ""),
                    "role": "",
                    "is_libero": "L" in parts[10:12] if len(parts) > 10 else False,
                    "shirt": int(parts[2]) if len(parts) > 2 and parts[2].lstrip("0").isdigit() else number,
                }
                if len(parts) > 11:
                    if parts[11].strip() == "L":
                        player["is_libero"] = True
                players.append(player)
        return players

    def _clean_name(self, raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("\\x"):
            raw = self._decode_hex_name(raw)
        raw = raw.replace("\\x00", "")
        raw = raw.strip()
        return raw

    def _parse_sets(self, sections: dict) -> list[list[int]]:
        sets = []
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
                        else:
                            if final_score is not None:
                                final_score[1] = int(score_part)
                            else:
                                final_score = [0, int(score_part)]
                    except (ValueError, IndexError):
                        continue
                if final_score:
                    sets.append(final_score)
        return sets

    def _parse_video(self, sections: dict) -> str:
        for line in sections.get("3VIDEO", []):
            if line.startswith("Camera0="):
                return line.split("=", 1)[1].strip()
        return ""

    def _migrate_schema(self):
        try:
            self.session.execute("ALTER TABLE scout_events ADD COLUMN rotation INTEGER DEFAULT 1")
        except Exception:
            pass
        try:
            self.session.execute("ALTER TABLE match_sets ADD COLUMN home_lineup TEXT DEFAULT NULL")
        except Exception:
            pass
        try:
            self.session.execute("ALTER TABLE match_sets ADD COLUMN away_lineup TEXT DEFAULT NULL")
        except Exception:
            pass

    def _parse_scout_lines(self, sections: dict) -> list:
        lines = []
        for raw in sections.get("3SCOUT", []):
            if raw.startswith("**") and "set" not in raw:
                continue
            lines.append(raw)
        return lines

    def _get_or_create_team(self, data: dict) -> Team:
        name = data.get("name", "Sconosciuta")
        team = self.session.query(Team).filter(Team.name == name).first()
        if not team:
            team = Team(
                name=name,
                short_name=data.get("code", name[:3].upper()),
            )
            self.session.add(team)
            self.session.flush()
        return team

    def _create_match(self, header: dict, home: Team, away: Team, video_path: str) -> Match | None:
        from sqlalchemy import func
        match_date = header.get("date", datetime.now())
        date_start = match_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = match_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        existing = (
            self.session.query(Match)
            .filter(
                Match.home_team_id == home.id,
                Match.away_team_id == away.id,
                Match.date >= date_start,
                Match.date <= date_end,
            )
            .first()
        )
        if existing is not None:
            logger.warning("Match duplicato trovato (id=%s), salto importazione", existing.id)
            return None
        match = Match(
            home_team_id=home.id,
            away_team_id=away.id,
            date=match_date,
            competition=header.get("competition", ""),
            venue=header.get("venue", ""),
            video_path=video_path or None,
            status="completed",
        )
        self.session.add(match)
        self.session.flush()
        return match

    def _import_players(self, player_data: list[dict], team: Team, match: Match):
        for pd in player_data:
            if pd["number"] == 0:
                continue
            existing = self.session.query(Player).filter(
                Player.team_id == team.id,
                Player.number == pd["number"],
            ).first()
            if not existing:
                player = Player(
                    team_id=team.id,
                    number=pd["number"],
                    last_name=pd.get("last_name", ""),
                    first_name=pd.get("first_name", ""),
                    role=pd.get("role", ""),
                    is_libero=pd.get("is_libero", False),
                )
                self.session.add(player)
                self.session.flush()

    def _create_sets(self, match: Match, set_scores: list[list[int]]):
        for i, scores in enumerate(set_scores, 1):
            if len(scores) >= 2:
                ms = MatchSet(
                    match_id=match.id,
                    set_number=i,
                    score_home=scores[0],
                    score_away=scores[1],
                )
                self.session.add(ms)
        self.session.flush()

    def _import_events(
        self,
        match: Match,
        home_team: Team,
        away_team: Team,
        scout_lines: list[str],
        set_scores: list[list[int]],
    ):
        current_set = 1
        score_home = 0
        score_away = 0
        rally = 0
        rotation_home = 1
        rotation_away = 1
        lineup_stored = set()  # set_numbers for which lineup was already stored
        setter_home: str | None = None
        setter_away: str | None = None

        for line in scout_lines:
            try:
                # Set number dal campo raw DWV [8] (più affidabile dei marker **Nset)
                parts = line.split(';')
                if len(parts) > 8:
                    raw_set_str = parts[8].strip()
                    if raw_set_str.isdigit():
                        raw_set = int(raw_set_str)
                        if 1 <= raw_set <= len(set_scores) and raw_set != current_set:
                            current_set = raw_set
                            score_home = 0
                            score_away = 0
                            rotation_home = 1
                            rotation_away = 1

                parsed = self._parse_scout_line(line)
                if not parsed or parsed.get("kind") == "set_marker":
                    continue
                kind = parsed["kind"]
                team_side = parsed["team_side"]

                if current_set not in lineup_stored:
                    lineup = self._extract_lineup(line)
                    if lineup:
                        self._store_lineup(match, current_set, lineup)
                        lineup_stored.add(current_set)

                if kind == "rotation":
                    if team_side == "home":
                        rotation_home = parsed["rotation"]
                    else:
                        rotation_away = parsed["rotation"]
                    continue

                if kind == "point":
                    ts = parsed.get("timestamp")
                    if ts is not None:
                        self.last_video_ts = ts
                    if parsed.get("score_home") is not None:
                        score_home = parsed["score_home"]
                        score_away = parsed["score_away"]
                        rot = rotation_home if team_side == "home" else rotation_away
                        event = ScoutEvent(
                            match_id=match.id,
                            set_id=self._set_id(match, current_set),
                            team_side="a" if team_side == "home" else "b",
                            score_home=score_home,
                            score_away=score_away,
                            video_timestamp=ts or (self.last_video_ts if self.last_video_ts > 0 else None),
                            rotation=rot,
                            notes=f"Punto {score_home}-{score_away}",
                            special_code="PT",
                        )
                        self.session.add(event)
                    continue

                if kind == "timeout":
                    ts = self._extract_timestamp(line)
                    rot = rotation_home if team_side == "home" else rotation_away
                    event = ScoutEvent(
                        match_id=match.id,
                        set_id=self._set_id(match, current_set),
                        team_side="a" if team_side == "home" else "b",
                        score_home=score_home,
                        score_away=score_away,
                        video_timestamp=ts or (self.last_video_ts if self.last_video_ts > 0 else None),
                        rotation=rot,
                        notes="Timeout",
                        special_code="SY",
                    )
                    self.session.add(event)
                    continue

                if kind == "substitution":
                    ts = self._extract_timestamp(line)
                    rot = rotation_home if team_side == "home" else rotation_away
                    p_in = parsed.get("player_in", "?")
                    p_out = parsed.get("player_out", "?")
                    event = ScoutEvent(
                        match_id=match.id,
                        set_id=self._set_id(match, current_set),
                        team_side="a" if team_side == "home" else "b",
                        score_home=score_home,
                        score_away=score_away,
                        video_timestamp=ts or (self.last_video_ts if self.last_video_ts > 0 else None),
                        rotation=rot,
                        notes=f"Sost. #{p_out} → #{p_in}",
                        special_code="SY",
                    )
                    self.session.add(event)
                    continue

                if kind == "player_position":
                    ts = self._extract_timestamp(line)
                    p_num = parsed.get("player_number", "?")
                    rot = rotation_home if team_side == "home" else rotation_away
                    event = ScoutEvent(
                        match_id=match.id,
                        set_id=self._set_id(match, current_set),
                        team_side="a" if team_side == "home" else "b",
                        score_home=score_home,
                        score_away=score_away,
                        video_timestamp=ts or (self.last_video_ts if self.last_video_ts > 0 else None),
                        rotation=rot,
                        notes=f"Posizione #{p_num}",
                        special_code="SY",
                    )
                    self.session.add(event)
                    continue

                if kind in ("formation", "formation_zone"):
                    # Linee formazione (P13>LUp, z4>LUp): i dati lineup/giratore
                    # sono già estratti dal loop principale; non generano eventi.
                    if kind == "formation":
                        pn = parsed.get("player_number")
                        if pn is not None:
                            if team_side == "home" and setter_home is None:
                                setter_home = str(pn)
                            elif team_side == "away" and setter_away is None:
                                setter_away = str(pn)
                    if kind == "formation_zone" and parsed.get("zone_number") is not None:
                        zn = parsed["zone_number"]
                        if 1 <= zn <= 6:
                            if team_side == "home":
                                rotation_home = zn
                            else:
                                rotation_away = zn
                    continue

                if kind == "action":
                    rally += 1
                    ts = self._extract_timestamp(line)
                    if ts is None and self.last_video_ts > 0:
                        ts = self.last_video_ts

                    skill_code = parsed.get("skill")
                    if skill_code and skill_code not in SKILL_MAP:
                        continue

                    player_num = parsed.get("player_number")

                    internal_skill = SKILL_MAP.get(skill_code, skill_code)
                    rot = rotation_home if team_side == "home" else rotation_away
                    eval_str = parsed.get("evaluation") or "-"
                    zone_str = ""
                    if parsed.get("zone_start") and parsed.get("zone_end"):
                        zone_str = f" Z{parsed['zone_start']}→{parsed['zone_end']}"
                    elif parsed.get("zone_start"):
                        zone_str = f" Z{parsed['zone_start']}"
                    player_str = f" #{player_num}" if player_num else ""
                    note = f"{skill_code}{eval_str}{zone_str}{player_str}"

                    event = ScoutEvent(
                        match_id=match.id,
                        set_id=self._set_id(match, current_set),
                        team_side="a" if team_side == "home" else "b",
                        skill=internal_skill,
                        evaluation=parsed.get("evaluation"),
                        zone_start=parsed.get("zone_start"),
                        zone_end=parsed.get("zone_end"),
                        attack_combo=parsed.get("attack_combo"),
                        score_home=score_home,
                        score_away=score_away,
                        video_timestamp=ts,
                        rally_number=rally,
                        rotation=rot,
                        notes=note,
                        special_code="SK",
                    )
                    if player_num:
                        player = self.session.query(Player).filter(
                            Player.team_id == (home_team.id if team_side == "home" else away_team.id),
                            Player.number == player_num,
                        ).first()
                        if player:
                            event.player_id = player.id

                    self.session.add(event)

            except Exception:
                logger.debug("Skipping unparsable line: %s", line[:60])
                continue

        # Imposta palleggiatore rilevato dalle linee P{n}>LUp
        if setter_home:
            self._store_setter_role(match, home_team, setter_home)
        if setter_away:
            self._store_setter_role(match, away_team, setter_away)

    def _store_setter_role(self, match: Match, team: Team, player_number: str):
        from volleyball_scout.core.models import MatchPlayer
        player = (
            self.session.query(Player)
            .filter(Player.team_id == team.id, Player.number == int(player_number))
            .first()
        )
        if player is None:
            return
        existing = (
            self.session.query(MatchPlayer)
            .filter_by(match_id=match.id, player_id=player.id)
            .first()
        )
        if existing is not None:
            if not existing.role:
                existing.role = "palleggiatore"
        else:
            mp = MatchPlayer(
                match_id=match.id,
                team_id=team.id,
                player_id=player.id,
                number=player.number,
                role="palleggiatore",
                is_starter=True,
            )
            self.session.add(mp)

    def _extract_lineup(self, line: str) -> dict | None:
        parts = line.split(";")
        if len(parts) < 26:
            return None
        home = {}
        away = {}
        pos_codes = ["P1", "P2", "P3", "P4", "P5", "P6"]
        home_nums = [p.strip() for p in parts[14:20]]
        away_nums = [p.strip() for p in parts[20:26]]
        if any(not n.isdigit() for n in home_nums + away_nums):
            return None
        for pos, num in zip(pos_codes, home_nums):
            home[pos] = num
        for pos, num in zip(pos_codes, away_nums):
            away[pos] = num
        return {"home": home, "away": away}

    def _store_lineup(self, match: Match, set_number: int, lineup: dict):
        from sqlalchemy import update
        import json
        stmt = (
            update(MatchSet)
            .where(
                MatchSet.match_id == match.id,
                MatchSet.set_number == set_number,
            )
            .values(
                home_lineup=json.dumps(lineup["home"]),
                away_lineup=json.dumps(lineup["away"]),
            )
        )
        self.session.execute(stmt)

    def _parse_scout_line(self, line: str) -> dict | None:
        if not line:
            return None

        team_side = "away" if line.startswith(("a", "A")) else "home"
        result = {"team_side": team_side}

        code_part = line.lstrip("*aAbB")

        if code_part.startswith("**"):
            return None

        if line.startswith("**") and "set" in line:
            m = re.search(r"\*\*(\d)set", line)
            if m:
                return {"kind": "set_marker", "set_number": int(m.group(1)), "team_side": team_side}
            return None

        # Linee di formazione/azioni speciali con ">" (es: P13>LUp, z4>LUp)
        if ">" in code_part:
            left, right = code_part.split(">", 1)
            action_code = right.strip()

            p_m = re.match(r"P(\d+)", left)
            if p_m:
                return {
                    "kind": "formation",
                    "team_side": team_side,
                    "player_number": int(p_m.group(1)),
                    "action_code": action_code,
                }

            z_m = re.match(r"z(\d)", left)
            if z_m:
                return {
                    "kind": "formation_zone",
                    "team_side": team_side,
                    "zone_number": int(z_m.group(1)),
                    "action_code": action_code,
                }

            return {"kind": "formation", "team_side": team_side, "action_code": action_code}

        m_p = re.match(r"P(\d+)", code_part)
        if m_p:
            return {"kind": "player_position", "team_side": team_side, "player_number": int(m_p.group(1))}

        if code_part.startswith("T"):
            return {"kind": "timeout", "team_side": team_side}

        m_sub = re.match(r"c(\d+):(\d+)", code_part)
        if m_sub:
            return {
                "kind": "substitution",
                "team_side": team_side,
                "player_in": int(m_sub.group(1)),
                "player_out": int(m_sub.group(2)),
            }

        m_z = re.match(r"z(\d)", code_part)
        if m_z:
            return {"kind": "rotation", "team_side": team_side, "rotation": int(m_z.group(1))}

        m_point = re.match(r"p(\d+):(\d+)", code_part)
        if m_point:
            score_home = int(m_point.group(1))
            score_away = int(m_point.group(2))
            ts = self._extract_timestamp(line)
            return {
                "kind": "point",
                "team_side": team_side,
                "score_home": score_home,
                "score_away": score_away,
                "timestamp": ts,
            }

        if code_part.startswith("$"):
            return {"kind": "point", "team_side": team_side}

        m_action = re.match(
            r"(\d{1,2})([A-Z]{2})([#+!\-=/]?)",
            code_part,
        )
        if m_action:
            result["kind"] = "action"
            result["player_number"] = int(m_action.group(1))
            result["skill"] = m_action.group(2)
            result["evaluation"] = m_action.group(3) or None

            rest = code_part[m_action.end():]
            combo_m = re.search(r"[~=]*([A-Z0-9]{1,4})", rest)
            if combo_m:
                combo_raw = combo_m.group(1)
                if len(combo_raw) >= 2:
                    result["attack_combo"] = combo_raw[:2]
                zone_m = re.search(r"(\d)(\d)", combo_raw)
                if zone_m:
                    result["zone_start"] = zone_m.group(1)
                    result["zone_end"] = zone_m.group(2)
                else:
                    single_z = re.search(r"(\d)", combo_raw)
                    if single_z:
                        result["zone_end"] = single_z.group(1)

            result["line_raw"] = code_part
            return result

        return None

    def _extract_timestamp(self, line: str) -> float | None:
        parts = line.split(";")
        if len(parts) > 7:
            ts_str = parts[7].strip()
            try:
                t = datetime.strptime(ts_str, "%H.%M.%S")
                abs_seconds = (t - datetime.strptime("00.00.00", "%H.%M.%S")).total_seconds()
                return abs_seconds - self.ts_reference
            except ValueError:
                return None
        return None

    def _set_id(self, match: Match, set_number: int) -> int | None:
        ms = (
            self.session.query(MatchSet)
            .filter(
                MatchSet.match_id == match.id,
                MatchSet.set_number == set_number,
            )
            .first()
        )
        return ms.id if ms else None

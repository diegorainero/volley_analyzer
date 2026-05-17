import json

from .datavolley_codes import normalize_lineup_number, find_player_position_in_lineup


class FormationManager:
    def __init__(self, db=None):
        self.db = db

    # ----- Reception positions persistence -----

    def reception_memory_key(
        self, side: str, match_id, set_number, settings_prefix: str
    ) -> str | None:
        try:
            parsed_match = int(str(match_id))
            parsed_set = int(str(set_number))
            if parsed_match <= 0 or parsed_set <= 0:
                return None
        except Exception:
            return None

        safe_side = "away" if side == "away" else "home"
        return (
            f"{settings_prefix}{parsed_match}"
            f"_set_{parsed_set}_{safe_side}"
        )

    def normalize_reception_positions(self, parsed) -> dict[str, tuple[float, float]]:
        if not isinstance(parsed, dict):
            return {}

        result: dict[str, tuple[float, float]] = {}
        for number, value in parsed.items():
            try:
                x, y = value
                result[str(number)] = (
                    min(1.0, max(0.0, float(x))),
                    min(1.0, max(0.0, float(y))),
                )
            except Exception:
                continue
        return result

    def load_reception_positions_from_db(
        self, side: str, match_id, set_number
    ) -> dict[str, tuple[float, float]]:
        if self.db is None:
            return {}

        safe_side = "away" if side == "away" else "home"
        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchSetReceptionLayout

                row = (
                    session.query(MatchSetReceptionLayout)
                    .filter_by(
                        match_id=int(match_id),
                        set_number=int(set_number),
                        team_side=safe_side,
                    )
                    .first()
                )
                if row is None or not getattr(row, "positions_json", None):
                    return {}

                parsed = json.loads(str(row.positions_json))
                return self.normalize_reception_positions(parsed)
        except Exception:
            return {}

    def load_reception_positions(
        self,
        side: str,
        match_id,
        set_number,
        settings,
        settings_prefix: str,
    ) -> dict[str, tuple[float, float]]:
        db_positions = self.load_reception_positions_from_db(side, match_id, set_number)
        if db_positions:
            return db_positions

        key = self.reception_memory_key(side, match_id, set_number, settings_prefix)
        if key is None:
            return {}

        raw = settings.value(key, None)
        if raw is None:
            return {}

        try:
            parsed = json.loads(str(raw))
        except Exception:
            return {}

        normalized = self.normalize_reception_positions(parsed)
        if normalized and self.db is not None:
            self.save_reception_positions(
                side, match_id, set_number, normalized, settings, settings_prefix
            )
        return normalized

    def save_reception_positions(
        self,
        side: str,
        match_id,
        set_number,
        positions: dict[str, tuple[float, float]],
        settings,
        settings_prefix: str,
    ):
        key = self.reception_memory_key(side, match_id, set_number, settings_prefix)
        serializable = {
            str(number): [float(value[0]), float(value[1])]
            for number, value in dict(positions or {}).items()
        }

        if key is not None:
            settings.setValue(key, json.dumps(serializable, ensure_ascii=False))

        if self.db is None:
            return

        from sqlalchemy import and_
        from volleyball_scout.core.models import MatchSetReceptionLayout

        with self.db.session_scope() as session:
            existing = (
                session.query(MatchSetReceptionLayout)
                .filter(
                    and_(
                        MatchSetReceptionLayout.match_id == int(match_id),
                        MatchSetReceptionLayout.set_number == int(set_number),
                        MatchSetReceptionLayout.team_side == side,
                    )
                )
                .first()
            )
            if existing:
                existing.positions_json = json.dumps(serializable)
            else:
                layout = MatchSetReceptionLayout(
                    match_id=int(match_id),
                    set_number=int(set_number),
                    team_side=side,
                    positions_json=json.dumps(serializable),
                )
                session.add(layout)

    # ----- Player data -----

    def get_player_roles(
        self, match_id, team_id
    ) -> dict[str, str]:
        if not team_id or not match_id or self.db is None:
            return {}
        try:
            from volleyball_scout.core.models import MatchPlayer
            with self.db.session_scope() as session:
                rows = (
                    session.query(MatchPlayer)
                    .filter_by(match_id=match_id, team_id=team_id)
                    .all()
                )
                result = {}
                for r in rows:
                    num = normalize_lineup_number(getattr(r, "number", None))
                    role = str(getattr(r, "role", "") or "").strip().lower()
                    if num:
                        result[num] = role
                return result
        except Exception:
            return {}

    def detect_setter_number(
        self,
        match_id,
        team_id,
        lineup_numbers: set[str],
        explicit_setter: str | None = None,
    ) -> str | None:
        if explicit_setter and explicit_setter in lineup_numbers:
            return explicit_setter

        if self.db is None:
            return None

        try:
            from volleyball_scout.core.models import MatchPlayer
            with self.db.session_scope() as session:
                rows = (
                    session.query(MatchPlayer)
                    .filter_by(match_id=match_id, team_id=team_id)
                    .all()
                )

                starters = [r for r in rows if bool(getattr(r, "is_starter", False))]
                ordered_sets = [starters, rows]
                for source_rows in ordered_sets:
                    for row in source_rows:
                        role_text = str(getattr(row, "role", "") or "").strip().lower()
                        if "palleggiatore" not in role_text:
                            continue
                        number = normalize_lineup_number(
                            getattr(row, "number", None)
                        )
                        if number in lineup_numbers:
                            return number
        except Exception:
            return None

        return None

    # ----- Auto-generation -----

    def auto_generate_reception_positions(
        self,
        lineup: dict[str, str],
        setter_number: str | None,
        roles: dict[str, str],
        team_id,
        game_method_by_team: dict,
        libero_number: str | None,
    ) -> dict | None:
        if len(lineup) < 6 or setter_number is None or not roles:
            return None

        method = game_method_by_team.get(str(team_id), "P-S-C") if team_id else "P-S-C"

        default_positions = {
            "1": (0.82, 0.82),
            "6": (0.50, 0.78),
            "5": (0.18, 0.82),
            "4": (0.18, 0.22),
            "3": (0.50, 0.22),
            "2": (0.82, 0.22),
        }

        back_row_zones = ["1", "6", "5"]
        back_players = {}
        for zone in back_row_zones:
            pos = f"P{zone}"
            num = lineup.get(pos)
            if num:
                back_players[zone] = num

        position5_player = None
        for zone in list(back_row_zones):
            num = back_players.get(zone)
            if num is None:
                continue
            if num == libero_number:
                position5_player = num
                back_row_zones.remove(zone)
                break
            role = roles.get(num, "")
            if "centrale" in role:
                if position5_player is None:
                    position5_player = num
                    back_row_zones.remove(zone)
                    break

        if position5_player is None:
            for zone in list(back_row_zones):
                num = back_players.get(zone)
                if num:
                    position5_player = num
                    back_row_zones.remove(zone)
                    break

        result = {}
        assigned_zones = set()

        setter_pos = find_player_position_in_lineup(lineup, setter_number)
        setter_zone = None
        if setter_pos and setter_pos[1].isdigit():
            setter_zone = setter_pos[1]

        for pos_code in ("P1", "P2", "P3", "P4", "P5", "P6"):
            num = lineup.get(pos_code)
            if num is None:
                continue
            zone = pos_code[1]
            if zone == setter_zone:
                result[num] = default_positions["2"]
                assigned_zones.add("2")
            elif num == position5_player:
                result[num] = default_positions["5"]
                assigned_zones.add("5")
            else:
                for z in ("1", "6", "4", "3"):
                    if z not in assigned_zones and z != "2" and z != "5" and z != setter_zone:
                        result[num] = default_positions[z]
                        assigned_zones.add(z)
                        break

        return result if len(result) >= 5 else None

    # ----- Formation persistence -----

    def load_formations(self, side: str, match_id, set_number) -> dict:
        if self.db is not None:
            try:
                from sqlalchemy import and_
                from volleyball_scout.core.models import MatchSetReceptionLayout
                with self.db.session_scope() as session:
                    row = (
                        session.query(MatchSetReceptionLayout)
                        .filter(
                            and_(
                                MatchSetReceptionLayout.match_id == match_id,
                                MatchSetReceptionLayout.set_number == set_number,
                                MatchSetReceptionLayout.team_side == side,
                            )
                        )
                        .first()
                    )
                    if row is not None and row.positions_json:
                        try:
                            data = json.loads(row.positions_json)
                            fb = data.get("formation_by_rotation", {})
                            result = {}
                            for r_str, pos_dict in fb.items():
                                result[int(r_str)] = {
                                    k: (float(v[0]), float(v[1]))
                                    for k, v in pos_dict.items()
                                }
                            return result
                        except Exception:
                            pass
            except Exception:
                pass
        return {}

    def save_formations(
        self, side: str, match_id, set_number, formations: dict
    ):
        if not formations:
            return

        data = {"formation_by_rotation": {}}
        for r, pos in formations.items():
            data["formation_by_rotation"][str(r)] = {
                k: [float(v[0]), float(v[1])] for k, v in pos.items()
            }
        positions_json = json.dumps(data)

        if self.db is not None:
            from sqlalchemy import and_
            from volleyball_scout.core.models import MatchSetReceptionLayout
            with self.db.session_scope() as session:
                existing = (
                    session.query(MatchSetReceptionLayout)
                    .filter(
                        and_(
                            MatchSetReceptionLayout.match_id == match_id,
                            MatchSetReceptionLayout.set_number == set_number,
                            MatchSetReceptionLayout.team_side == side,
                        )
                    )
                    .first()
                )
                if existing:
                    existing.positions_json = positions_json
                else:
                    layout = MatchSetReceptionLayout(
                        match_id=match_id,
                        set_number=set_number,
                        team_side=side,
                        positions_json=positions_json,
                    )
                    session.add(layout)

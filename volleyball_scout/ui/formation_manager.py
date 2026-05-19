import json
import logging

logger = logging.getLogger(__name__)
import itertools

from .datavolley_codes import normalize_lineup_number, find_player_position_in_lineup


class FormationManager:
    def __init__(self, db=None):
        """Inizializza il gestore formazioni."""
        self.db = db

    # ----- Reception positions persistence -----

    def reception_memory_key(
        self, side: str, match_id, set_number, settings_prefix: str
    ) -> str | None:
        """Genera la chiave di memoria per le ricezioni."""
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
        """Normalizza le posizioni di ricezione."""
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
        """Carica le posizioni di ricezione dal DB."""
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
        """Carica le posizioni di ricezione."""
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
        """Salva le posizioni di ricezione."""
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
        """Recupera i ruoli dei giocatori."""
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
        """Individua il numero del palleggiatore."""
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
        """Genera automaticamente le posizioni di ricezione."""
        if len(lineup) < 6 or setter_number is None or not roles:
            return None

        method = game_method_by_team.get(str(team_id), "P-S-C") if team_id else "P-S-C"

        default_positions = {
            "1": (0.20, 0.80),  # back-right
            "6": (0.20, 0.50),  # back-center
            "5": (0.20, 0.20),  # back-left
            "4": (0.80, 0.20),  # front-left
            "3": (0.80, 0.50),  # front-center
            "2": (0.80, 0.80),  # front-right
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

        final = result if len(result) >= 5 else None
        logger.debug("auto_generate_reception_positions setter_zone=%s pos5=%s -> %s", setter_zone, position5_player, final)
        return final

    # ----- Formation persistence -----

    def load_formations(self, side: str, match_id, set_number) -> dict:
        """Carica le formazioni salvate."""
        logger.debug("load_formations side=%s match=%s set=%s", side, match_id, set_number)
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
                            logger.debug("load_formations OK side=%s rotations=%s", side, sorted(result.keys()))
                            return result
                        except Exception as e:
                            logger.warning("load_formations parse error: %s", e)
                            pass
            except Exception as e:
                logger.warning("load_formations db error: %s", e)
                pass
        logger.debug("load_formations empty side=%s", side)
        return {}

    def save_formations(
        self, side: str, match_id, set_number, formations: dict
    ):
        """Salva le formazioni."""
        if not formations:
            logger.debug("save_formations skip empty side=%s", side)
            return

        logger.debug("save_formations side=%s match=%s set=%s rotations=%s",
                      side, match_id, set_number, sorted(formations.keys()))
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

    # ----- Reception formation config -----

    ROLE_CODES = ["P", "S1", "S2", "C1", "C2", "O"]
    POS_CODES = ["P1", "P2", "P3", "P4", "P5", "P6"]

    ZONE_POSITIONS = [
        (0.20, 0.80),  # zone 1 (P1) - back-right
        (0.80, 0.80),  # zone 2 (P2) - front-right
        (0.80, 0.50),  # zone 3 (P3) - front-center
        (0.80, 0.20),  # zone 4 (P4) - front-left
        (0.20, 0.20),  # zone 5 (P5) - back-left
        (0.20, 0.50),  # zone 6 (P6) - back-center
    ]

    def generate_formation_from_scheme(self, scheme: str, rotation: int) -> dict:
        """Genera una formazione dallo schema."""
        base_role_order = {
            "P-S-C": ["P", "S1", "C2", "O", "S2", "C1"],
            "P-C-S": ["P", "C1", "S2", "O", "C2", "S1"],
        }
        roles = base_role_order.get(scheme, base_role_order["P-S-C"])
        shift = (rotation - 1) % 6
        rotated = roles[-shift:] + roles[:-shift]
        result = {rotated[i]: self.ZONE_POSITIONS[i] for i in range(6)}
        logger.debug("generate_formation_from_scheme scheme=%s rot=%s -> %s", scheme, rotation, result)
        return result

    def generate_all_rotations(self, scheme: str) -> dict:
        """Genera le formazioni per tutte le rotazioni."""
        result = {}
        for r in range(1, 7):
            result[r] = self.generate_formation_from_scheme(scheme, r)
        return result

    @staticmethod
    def is_old_format_config(config: dict) -> bool:
        """Verifica se la configurazione è in vecchio formato."""
        for rot, data in config.items():
            if isinstance(data, dict):
                for key in data:
                    if isinstance(key, str) and key.startswith("P") and len(key) == 2 and key[1].isdigit():
                        return True
        return False

    @staticmethod
    def convert_to_new_format(old_config: dict) -> dict:
        """Converte la configurazione nel nuovo formato."""
        pos_to_zone = {
            "P1": 0, "P2": 1, "P3": 2,
            "P4": 3, "P5": 4, "P6": 5,
        }
        zone_pos = FormationManager.ZONE_POSITIONS
        new_config = {}
        for rot, data in old_config.items():
            new_data = {}
            for pos, role in data.items():
                zi = pos_to_zone.get(pos)
                if zi is not None:
                    new_data[role] = zone_pos[zi]
            new_config[rot] = new_data
        return new_config

    def resolve_formation_player_assignments(
        self,
        lineup: dict[str, str],
        roles: dict[str, str],
        formation_config: dict,
        rotation: int,
        libero_number: str | None = None,
        known_setter: str | None = None,
    ) -> dict[str, tuple[float, float]] | None:
        """Assegna i giocatori alle posizioni dello schema."""
        rot_map = formation_config.get(rotation)
        if not rot_map:
            logger.debug("resolve no config for rotation %s", rotation)
            return None

        player_role_map = self._map_players_to_role_codes(lineup, roles, libero_number, known_setter=known_setter)
        if not player_role_map:
            logger.debug("resolve empty player_role_map for rotation %s", rotation)
            return None

        result = {}
        for player_num, role_code in player_role_map.items():
            xy = rot_map.get(role_code)
            if xy is not None:
                result[player_num] = xy

        logger.debug("resolve_formation: rot=%s role_map=%s result=%s", rotation, player_role_map, result)
        return result if len(result) >= 5 else None

    def _map_players_to_role_codes(
        self,
        lineup: dict[str, str],
        roles: dict[str, str],
        libero_number: str | None = None,
        known_setter: str | None = None,
    ) -> dict[str, str]:
        # Mappa i giocatori ai codici ruolo.
        ROLE_MAP = {
            "palleggiatore": None,
            "schiacciatore": None,
            "banda": None,
            "centrale": None,
            "opposto": "O",
            "libero": None,
        }

        assigned = {}
        players_with_roles = {}

        for pos, num in lineup.items():
            if num is None:
                continue
            ns = str(num).strip()
            if ns == str(libero_number or "").strip():
                continue
            db_role = roles.get(ns, "").strip().lower()
            players_with_roles[ns] = db_role

        setter = None
        opposites = []
        hitters = []
        middles = []

        known_setter_stripped = str(known_setter).strip() if known_setter else None
        for num, db_role in players_with_roles.items():
            if "palleggiatore" in db_role:
                if setter is None:
                    setter = num
                    assigned[num] = "P"
            elif "opposto" in db_role:
                if known_setter_stripped is None or num != known_setter_stripped:
                    opposites.append(num)
            elif "schiacciatore" in db_role or "banda" in db_role:
                if known_setter_stripped is None or num != known_setter_stripped:
                    hitters.append(num)
            elif "centrale" in db_role:
                if known_setter_stripped is None or num != known_setter_stripped:
                    middles.append(num)

        if setter is None:
            if known_setter is not None and str(known_setter).strip() in players_with_roles:
                setter = str(known_setter).strip()
                assigned[setter] = "P"
            else:
                return {}

        for i, num in enumerate(opposites):
            if len(opposites) == 1 or i == 0:
                assigned[num] = "O"

        role_hints = self._assign_s1_s2_from_lineup(lineup, setter, hitters)
        for num, hint in role_hints.items():
            assigned[num] = hint

        role_hints_c = self._assign_c1_c2_from_lineup(lineup, setter, middles)
        for num, hint in role_hints_c.items():
            assigned[num] = hint

        unassigned = [n for n in players_with_roles if n not in assigned]
        for num in unassigned:
            if hitters and num in hitters:
                assigned[num] = "S2"
            elif middles and num in middles:
                assigned[num] = "C2"
            elif opposites and num in opposites:
                assigned[num] = "O"
            else:
                assigned[num] = "S2"

        seen_roles = set()
        dedup = {}
        for num, rc in assigned.items():
            if rc not in seen_roles:
                seen_roles.add(rc)
                dedup[num] = rc
        available = [c for c in ["O", "S2", "C2", "S1", "C1"] if c not in seen_roles]
        for num, rc in list(assigned.items()):
            if num not in dedup:
                if available:
                    dedup[num] = available.pop(0)
                else:
                    dedup[num] = "S2"

        return dedup

    def _assign_s1_s2_from_lineup(
        self, lineup: dict[str, str], setter: str, hitters: list[str]
    ) -> dict[str, str]:
        # Assegna S1/S2 ai schiacciatori.
        result = {}
        if not hitters:
            return result

        setter_pos = find_player_position_in_lineup(lineup, setter)
        if not setter_pos:
            for i, num in enumerate(hitters):
                result[num] = "S1" if i == 0 else "S2"
            return result

        pos_order = ["P1", "P2", "P3", "P4", "P5", "P6"]
        setter_idx = pos_order.index(setter_pos) if setter_pos in pos_order else -1

        hitter_positions = []
        for pos in pos_order:
            num = lineup.get(pos)
            if num in hitters:
                hitter_positions.append((pos, num))

        if not hitter_positions:
            return result

        sorted_hitters = sorted(
            hitter_positions,
            key=lambda x: abs(pos_order.index(x[0]) - setter_idx) if setter_idx >= 0 else 0,
        )

        for i, (pos, num) in enumerate(sorted_hitters):
            result[num] = "S1" if i == 0 else "S2"

        return result

    def _assign_c1_c2_from_lineup(
        self, lineup: dict[str, str], setter: str, middles: list[str]
    ) -> dict[str, str]:
        # Assegna C1/C2 ai centrali.
        result = {}
        if not middles:
            return result

        setter_pos = find_player_position_in_lineup(lineup, setter)
        if not setter_pos:
            for i, num in enumerate(middles):
                result[num] = "C1" if i == 0 else "C2"
            return result

        pos_order = ["P1", "P2", "P3", "P4", "P5", "P6"]
        setter_idx = pos_order.index(setter_pos) if setter_pos in pos_order else -1

        middle_positions = []
        for pos in pos_order:
            num = lineup.get(pos)
            if num in middles:
                middle_positions.append((pos, num))

        if not middle_positions:
            return result

        sorted_middles = sorted(
            middle_positions,
            key=lambda x: abs(pos_order.index(x[0]) - setter_idx) if setter_idx >= 0 else 0,
        )

        for i, (pos, num) in enumerate(sorted_middles):
            result[num] = "C1" if i == 0 else "C2"

        return result

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

SKILL_CATEGORIES = {
    "S": {"label": "Battuta", "color": "#2196F3", "icon": "S"},
    "R": {"label": "Ricezione", "color": "#4CAF50", "icon": "R"},
    "E": {"label": "Alzata", "color": "#00BCD4", "icon": "E"},
    "A": {"label": "Attacco", "color": "#F44336", "icon": "A"},
    "B": {"label": "Muro", "color": "#9C27B0", "icon": "B"},
    "D": {"label": "Difesa", "color": "#E91E63", "icon": "D"},
    "F": {"label": "Free Ball", "color": "#FF9800", "icon": "F"},
}

EVALUATIONS = {
    "#": {"label": "Ace / Punto diretto", "color": "#4CAF50", "short": "#"},
    "+": {"label": "Buono / Positivo", "color": "#8BC34A", "short": "+"},
    "!": {"label": "Discreto / Sufficiente", "color": "#FFC107", "short": "!"},
    "-": {"label": "Negativo / Imperfetto", "color": "#FF9800", "short": "-"},
    "=": {"label": "Errore / Sbagliato", "color": "#F44336", "short": "="},
    "/": {"label": "Murato / Bloccato", "color": "#9C27B0", "short": "/"},
}


@dataclass(frozen=True)
class DVCode:
    code: str
    category: str
    label: str
    description: str
    color: str = "#999999"

    @property
    def category_info(self) -> dict:
        return SKILL_CATEGORIES.get(self.category, {})


DV_CODES: list[DVCode] = [
    DVCode("SQ", "S", "Battuta", "Servizio da fondo campo", "#2196F3"),
    DVCode("RQ", "R", "Ricezione", "Ricezione del servizio", "#4CAF50"),
    DVCode("SE", "E", "Alzata", "Alzata del palleggiatore", "#00BCD4"),
    DVCode("AH", "A", "Attacco H", "Attacco in posto 4/2 (laterale)", "#F44336"),
    DVCode("AU", "A", "Attacco U", "Attacco in posto 4/2 (universale)", "#E57373"),
    DVCode("AM", "A", "Attacco M", "Attacco centrale / da posto 3", "#EF5350"),
    DVCode("AQ", "A", "Attacco Q", "Attacco veloce / quick", "#FF5252"),
    DVCode("AO", "A", "Attacco O", "Attacco opposto / da posto 2", "#FF1744"),
    DVCode("TT", "A", "Appoggio", "Pallonetto / tip", "#FF8A65"),
    DVCode("FU", "F", "Free Ball", "Palla alta in attacco", "#FF9800"),
    DVCode("FH", "F", "Free Ball H", "Palla alta forzata", "#FFB74D"),
    DVCode("BH", "B", "Muro H", "Muro in posto 4/2", "#9C27B0"),
    DVCode("BM", "B", "Muro M", "Muro centrale", "#AB47BC"),
    DVCode("BO", "B", "Muro O", "Muro opposto", "#CE93D8"),
    DVCode("BD", "B", "Muro D", "Muro in difesa", "#BA68C8"),
    DVCode("DH", "D", "Difesa H", "Difesa in posto 1/5/6", "#E91E63"),
    DVCode("EH", "E", "Alzata H", "Alzata valutazione palleggiatore", "#26C6DA"),
    DVCode("EU", "E", "Alzata U", "Alzata di emergenza", "#4DD0E1"),
    DVCode("EQ", "E", "Alzata Q", "Alzata veloce", "#00ACC1"),
    DVCode("EO", "E", "Alzata O", "Alzata opposto", "#00838F"),
    DVCode("EM", "E", "Alzata M", "Alzata da centrale", "#006064"),
    DVCode("EP", "E", "Alzata P", "Alzata su pipe", "#00B8D4"),
    DVCode("SH", "S", "Battuta H", "Battuta in salto", "#1E88E5"),
    DVCode("SM", "S", "Battuta M", "Battuta in salto flot", "#42A5F5"),
    DVCode("SF", "S", "Battuta F", "Battuta flot", "#64B5F6"),
]


@dataclass(frozen=True)
class AttackCombo:
    code: str
    label: str
    description: str
    color: str = "#FFD54F"


ATTACK_COMBOS: list[AttackCombo] = [
    AttackCombo("X1", "Veloce Davanti", "Quick davanti in posto 3/4"),
    AttackCombo("X2", "Veloce Dietro", "Quick dietro in posto 2/3"),
    AttackCombo("XM", "Veloce 3", "Veloce in punto 3"),
    AttackCombo("XG", "Gun 7-1", "7-1 Gun"),
    AttackCombo("XC", "Veloce Spostata", "Veloce spostata dal palleggiatore"),
    AttackCombo("XD", "Doppia C", "Doppia veloce"),
    AttackCombo("X7", "Sette Davanti", "Sette davanti"),
    AttackCombo("XS", "Sette Dietro", "Sette dietro"),
    AttackCombo("XO", "Veloce Opposto", "Veloce per opposto"),
    AttackCombo("XF", "Fast Opposto", "Fast per opposto"),
    AttackCombo("X9", "Mezza 7", "Mezza davanti dopo 7"),
    AttackCombo("XT", "Mezza 4", "Mezza da posto 4"),
    AttackCombo("X3", "Mezza 2", "Mezza da posto 2"),
    AttackCombo("X4", "Mezza CA", "Mezza dietro C.A."),
    AttackCombo("XQ", "Mezza CD", "Mezza dietro C.D."),
    AttackCombo("XB", "Pipe 6-1", "Pipe spostata 6-1"),
    AttackCombo("XP", "Pipe", "Pipe da posto 6"),
    AttackCombo("XR", "Pipe 6-5", "Pipe spostata 6-5"),
    AttackCombo("X5", "Spinta 4", "Spinta in posto 4"),
    AttackCombo("X0", "Spinta 5", "Spinta in posto 5"),
    AttackCombo("X6", "Spinta 2", "Spinta in posto 2"),
    AttackCombo("X8", "Spinta 1", "Spinta in posto 1"),
    AttackCombo("CD", "Fast Vicino", "Fast vicino al palleggiatore"),
    AttackCombo("CB", "Fast Spostata", "Fast spostata dal palleggiatore"),
    AttackCombo("CF", "Fast Lontano", "Fast lontano dal palleggiatore"),
    AttackCombo("C5", "Super 4", "Super in posto 4"),
    AttackCombo("C0", "Super 5", "Super in posto 5"),
    AttackCombo("C6", "Super 2", "Super in posto 2"),
    AttackCombo("C8", "Super 1", "Super in posto 1"),
    AttackCombo("V5", "Alta 4", "Alta in posto 4"),
    AttackCombo("V0", "Alta 5", "Alta in posto 1"),
    AttackCombo("V6", "Alta 2", "Alta in posto 2"),
    AttackCombo("V8", "Alta 1", "Alta in posto 1"),
    AttackCombo("VB", "Pipe Alta 6-1", "Pipe alta spostata 6-1"),
    AttackCombo("VP", "Pipe Alta", "Pipe alta"),
    AttackCombo("VR", "Pipe Alta 6-5", "Pipe alta spostata 6-5"),
    AttackCombo("V3", "Alta 3", "Alta in posto 3"),
    AttackCombo("P2", "2° Tocco", "Secondo tocco del palleggiatore"),
    AttackCombo("PR", "Rigore", "Rigore"),
    AttackCombo("PP", "Pallonetto", "Pallonetto dell'alzatore"),
    AttackCombo("P3", "3° Tocco", "Terzo tocco di difesa"),
]


@dataclass(frozen=True)
class SetterCall:
    code: str
    label: str
    description: str
    color: str = "#B2EBF2"


SETTER_CALLS: list[SetterCall] = [
    SetterCall("K1", "Veloce Davanti", "Chiamata veloce davanti"),
    SetterCall("K2", "Veloce Dietro", "Chiamata veloce dietro"),
    SetterCall("K7", "Sette", "Chiamata sette"),
    SetterCall("KC", "Veloce 3", "Chiamata veloce in punto 3"),
    SetterCall("KM", "Spostata 2", "Chiamata spostata in 2"),
    SetterCall("KP", "Spostata 4", "Chiamata spostata verso 4"),
    SetterCall("KE", "No 1° Tempo", "Nessun primo tempo"),
    SetterCall("KF", "Fast", "Chiamata fast"),
]


COURT_ZONES = {
    1: {"label": "Zona 1", "pos": "DD-DX", "row": 3, "col": 3},
    2: {"label": "Zona 2", "pos": "AD-DX", "row": 1, "col": 3},
    3: {"label": "Zona 3", "pos": "AD-C", "row": 1, "col": 2},
    4: {"label": "Zona 4", "pos": "AD-SX", "row": 1, "col": 1},
    5: {"label": "Zona 5", "pos": "DD-SX", "row": 3, "col": 1},
    6: {"label": "Zona 6", "pos": "DD-C", "row": 3, "col": 2},
    7: {"label": "Zona 7 (fuori)", "pos": "Out SX", "row": 0, "col": 0},
    8: {"label": "Zona 8 (centro)", "pos": "Pipe", "row": 2, "col": 2},
    9: {"label": "Zona 9 (fuori)", "pos": "Out DX", "row": 0, "col": 4},
}


SERVE_ZONE_MAP = {
    "1": "Zona 1 (DD-DX)",
    "5": "Zona 5 (DD-SX)",
    "6": "Zona 6 (DD-C)",
    "9": "Zona 9 (Out DX)",
    "4": "Zona 4 (AD-SX)",
}


ATTACK_ZONE_MAP = {
    "4": "Posto 4 (AD-SX)",
    "3": "Posto 3 (AD-C)",
    "2": "Posto 2 (AD-DX)",
    "6": "Posto 6 (Pipe)",
    "1": "Posto 1 (DD-DX)",
    "5": "Posto 5 (DD-SX)",
    "8": "Posto 8 (Centro/CV)",
    "9": "Posto 9 (Out DX)",
}


ROTATION_POSITIONS = {
    1: {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6},
    2: {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 1},
    3: {1: 3, 2: 4, 3: 5, 4: 6, 5: 1, 6: 2},
    4: {1: 4, 2: 5, 3: 6, 4: 1, 5: 2, 6: 3},
    5: {1: 5, 2: 6, 3: 1, 4: 2, 5: 3, 6: 4},
    6: {1: 6, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5},
}


def rotation_to_lineup(rotation: int, base_lineup: dict[str, str]) -> dict[str, str]:
    mapping = ROTATION_POSITIONS.get(rotation, ROTATION_POSITIONS[1])
    result: dict[str, str] = {}
    zone_map = {"P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5, "P6": 6}
    zone_rev = {v: k for k, v in zone_map.items()}
    for zone_pos, court_zone in zone_map.items():
        home_zone = mapping[court_zone]
        home_pos = zone_rev[home_zone]
        result[zone_pos] = base_lineup.get(home_pos, "-")
    return result


def find_dv_code(code: str) -> DVCode | None:
    for dv in DV_CODES:
        if dv.code == code:
            return dv
    return None


def find_attack_combo(code: str) -> AttackCombo | None:
    for ac in ATTACK_COMBOS:
        if ac.code == code:
            return ac
    return None


def describe_trajectory(start_zone: str | None, end_zone: str | None, skill: str | None = None, end_on_opponent_court: bool | None = None) -> str:
    parts = []
    if skill == "R":
        return ""
    if start_zone:
        if skill == "S":
            desc = SERVE_ZONE_MAP.get(start_zone, f"Zona {start_zone}")
        else:
            desc = ATTACK_ZONE_MAP.get(start_zone, f"Zona {start_zone}")
        parts.append(f"Da {desc}")
    if end_zone:
        desc = ATTACK_ZONE_MAP.get(end_zone, f"Zona {end_zone}")
        if end_on_opponent_court is True:
            desc += " (campo avversario)"
        elif end_on_opponent_court is False:
            desc += " (errore)"
        parts.append(f"→ {desc}")
    return " ".join(parts) if parts else ""


SKILL_MAP_INTERNAL = {
    "SQ": "S", "SM": "S", "SF": "S", "SH": "S",
    "RQ": "R",
    "SE": "E", "EH": "E", "EU": "E", "EQ": "E", "EO": "E", "EM": "E", "EP": "E",
    "AH": "A", "AU": "A", "AM": "A", "AQ": "A", "AO": "A", "TT": "A",
    "FU": "F", "FH": "F",
    "BH": "B", "BM": "B", "BO": "B", "BD": "B",
    "DH": "D",
}

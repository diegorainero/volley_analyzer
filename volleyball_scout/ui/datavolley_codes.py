import re
from copy import deepcopy


def infer_code_team_side(normalized: str) -> str | None:
    """Inferisce il lato squadra dal codice DataVolley."""
    scan_code = str(normalized or "").strip().upper().replace(" ", "")
    if not scan_code:
        return None
    if scan_code[0] == "*":
        return "home"
    if (
        len(scan_code) > 1
        and scan_code[0] == "A"
        and (scan_code[1].isdigit() or scan_code[1] == "P")
    ):
        return "home"
    if (
        len(scan_code) > 1
        and scan_code[0] == "B"
        and (scan_code[1].isdigit() or scan_code[1] == "P")
    ):
        return "away"
    return None


def parse_datavolley_code(
    raw_code: str,
    skill_aliases: dict[str, str],
    evaluations: set[str],
) -> dict:
    """Analizza un codice DataVolley grezzo."""
    normalized = str(raw_code or "").strip().upper().replace(" ", "")
    if not normalized:
        return {"valid": False, "error": "Codice vuoto"}

    guessed_team = infer_code_team_side(normalized)
    team_side = guessed_team

    scan_code = normalized
    if scan_code and scan_code[0] == "*":
        scan_code = scan_code[1:]
    elif (
        len(scan_code) > 1
        and scan_code[0] in {"A", "B"}
        and (scan_code[1].isdigit() or scan_code[1] == "P")
    ):
        scan_code = scan_code[1:]

    if not scan_code:
        return {"valid": False, "error": "Codice incompleto"}

    skill_index = None
    skill = None
    for idx, ch in enumerate(scan_code):
        if ch in skill_aliases:
            skill_index = idx
            skill = skill_aliases[ch]
            break

    if skill_index is None or skill is None:
        return {
            "valid": False,
            "error": "Skill DataVolley non trovata (usa S/R/E/A/B/D/F)",
        }

    prefix_part = scan_code[:skill_index]
    suffix_part = scan_code[skill_index + 1:]

    player_number = None
    player_match = re.search(r"(\d{1,2})$", prefix_part)
    if player_match:
        player_number = player_match.group(1).zfill(2)

    evaluation = None
    if suffix_part and suffix_part[0] in evaluations:
        evaluation = suffix_part[0]
        suffix_part = suffix_part[1:]

    zone_start = None
    zone_end = None
    extra_part = suffix_part
    zone_pair_match = re.search(r"([1-9])([1-9])$", suffix_part)
    if zone_pair_match:
        zone_start = zone_pair_match.group(1)
        zone_end = zone_pair_match.group(2)
        extra_part = suffix_part[:-2]

    extra_part = extra_part.strip()
    attack_combo = None
    set_code = None
    if extra_part:
        extra_match = re.search(r"([A-Z0-9]{1,2})$", extra_part)
        if extra_match:
            if skill == "A":
                attack_combo = extra_match.group(1)
            elif skill == "E":
                set_code = extra_match.group(1)

    return {
        "valid": True,
        "raw": normalized,
        "team_side": team_side,
        "player_number": player_number,
        "skill": skill,
        "evaluation": evaluation,
        "zone_start": zone_start,
        "zone_end": zone_end,
        "attack_combo": attack_combo,
        "set_code": set_code,
    }


def resolve_point_team_from_evaluation(
    side: str,
    skill: str | None,
    evaluation: str | None,
    point_outcome_map: dict[str, str],
    skill_aliases: dict[str, str] | None = None,
) -> str | None:
    """Determina chi ha fatto punto dalla valutazione."""
    eval_token = str(evaluation or "").strip()
    if not eval_token:
        return None

    skill_token = str(skill or "").strip().upper()
    if skill_aliases and skill_token not in skill_aliases:
        skill_token = "*"
    elif not skill_aliases and skill_token not in {"S", "R", "E", "A", "B", "D", "F", "*"}:
        pass

    key_specific = f"{skill_token}{eval_token}"
    key_fallback = f"*{eval_token}"
    outcome = point_outcome_map.get(key_specific)
    if outcome is None:
        outcome = point_outcome_map.get(key_fallback)

    outcome = str(outcome or "none").strip().lower()
    if outcome == "self":
        return side
    if outcome == "opponent":
        return "away" if side == "home" else "home"
    return None


def default_point_outcome_map() -> dict[str, str]:
    """Mappa predefinita esiti punto per skill."""
    return {
        "*#": "self",
        "*=": "opponent",
        "S#": "self",
        "S=": "opponent",
        "R#": "none",
        "R=": "opponent",
    }


def decode_point_outcome_map(
    serialized: str | None,
    base_map: dict[str, str] | None = None,
) -> dict[str, str]:
    """Decodifica mappa esiti da testo serializzato."""
    result = dict(base_map) if base_map is not None else default_point_outcome_map()
    if not str(serialized or "").strip():
        return result

    for line in str(serialized).splitlines():
        row = line.strip()
        if not row or "|" not in row:
            continue
        key, value = row.split("|", 1)
        key = str(key).strip().upper()
        value = str(value).strip().lower()
        if re.fullmatch(r"[SREABDF\*][#\+!\-=/]", key) and value in {
            "self",
            "opponent",
            "none",
        }:
            result[key] = value
    return result


def point_outcome_map_to_text(rules: dict[str, str]) -> str:
    """Converte mappa esiti in testo leggibile."""
    rows = [
        "# Formato: SkillValutazione=esito",
        "# Esito: self | opponent | none",
        "# Esempi:",
        "# S#=self      -> punto a chi esegue la battuta",
        "# R==opponent  -> errore ricezione, punto all'avversario",
        "# *#=self      -> fallback per qualsiasi skill con #",
        "",
    ]
    for key in sorted(rules.keys()):
        rows.append(f"{key}={rules[key]}")
    return "\n".join(rows)


def parse_point_outcome_map_text(text: str) -> dict[str, str]:
    """Analizza testo mappa esiti in dict."""
    result = default_point_outcome_map()
    if not str(text or "").strip():
        return result
    for line in str(text).splitlines():
        row = line.strip()
        if not row or "=" not in row:
            continue
        key, value = row.split("=", 1)
        key = str(key).strip().upper()
        value = str(value).strip().lower()
        if re.fullmatch(r"[SREABDF\*][#\+!\-=/]", key) and value in {
            "self",
            "opponent",
            "none",
        }:
            result[key] = value
    return result


def normalize_lineup_number(value) -> str | None:
    """Normalizza numero maglia in formato stringa."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw or raw == "-":
        return None
    try:
        return str(int(raw))
    except Exception:
        return raw.lstrip("0") or raw


def lineup_numbers_for_side(lineup: dict) -> list[str]:
    """Estrae numeri maglia ordinati dal lineup."""
    ordered = []
    for pos in ("P1", "P2", "P3", "P4", "P5", "P6"):
        normalized = normalize_lineup_number(lineup.get(pos))
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    return ordered


def find_player_position_in_lineup(
    lineup: dict, player_number
) -> str | None:
    """Trova posizione giocatore nel lineup."""
    target = normalize_lineup_number(player_number)
    if target is None:
        return None
    for pos in ("P1", "P2", "P3", "P4", "P5", "P6"):
        if normalize_lineup_number(lineup.get(pos)) == target:
            return pos
    return None

from __future__ import annotations

from typing import Any, Mapping

# Mapping di rotazione oraria in campo (old -> new)
# Equivalente al comportamento usato nel FormationPanel.
ROTATION_POSITION_MAP: dict[str, str] = {
    "P1": "P6",
    "P2": "P1",
    "P3": "P2",
    "P4": "P3",
    "P5": "P4",
    "P6": "P5",
}

# Stesso mapping ma per gli indici slot del FormationPanel:
# 0=P1, 1=P2, 2=P3, 3=P4, 4=P5, 5=P6
ROTATION_INDEX_MAP: dict[int, int] = {0: 5, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4}


def rotate_lineup_clockwise(lineup: Mapping[str, Any] | None) -> dict[str, Any]:
    """Ruota una lineup per posizioni P1..P6 in senso orario.

    Restituisce sempre un nuovo dict senza mutare l'input.
    """
    source = dict(lineup or {})
    rotated = dict(source)

    for old_pos, new_pos in ROTATION_POSITION_MAP.items():
        rotated[new_pos] = source.get(old_pos)

    return rotated


def rotate_slots_clockwise(slots: Mapping[int, Any] | None) -> dict[int, Any]:
    """Ruota una mappa slot indicizzata (0..5) in senso orario.

    Restituisce sempre un nuovo dict senza mutare l'input.
    """
    source = dict(slots or {})
    rotated = dict(source)

    for old_idx, new_idx in ROTATION_INDEX_MAP.items():
        rotated[new_idx] = source.get(old_idx)

    return rotated


def get_current_rotation(
    lineup: Mapping[str, Any] | None, setter_number: str | int | None
) -> int | None:
    """Determina il numero di rotazione corrente (1-6) dalla posizione del palleggiatore.

    Rotation 1 = palleggiatore in P1 (fila dietro, destra)
    Rotation 2 = palleggiatore in P2 (fila davanti, destra)
    Rotation 3 = palleggiatore in P3 (fila davanti, centro)
    Rotation 4 = palleggiatore in P4 (fila davanti, sinistra)
    Rotation 5 = palleggiatore in P5 (fila dietro, sinistra)
    Rotation 6 = palleggiatore in P6 (fila dietro, centro)
    """
    if setter_number is None or lineup is None:
        return None
    target = str(setter_number).strip()
    for pos_code in ("P1", "P2", "P3", "P4", "P5", "P6"):
        if str(lineup.get(pos_code, "")).strip() == target:
            return int(pos_code[1])
    return None

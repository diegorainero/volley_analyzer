from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class Detection:
    bbox: tuple[float, float, float, float]
    confidence: float
    class_name: str = "player"
    team_id: str | None = None
    mask: np.ndarray | None = None


@dataclass(slots=True)
class Track:
    track_id: int
    bbox: tuple[float, float, float, float]
    confidence: float
    team_id: str | None = None
    jersey_number: str | None = None
    field_position: tuple[float, float] | None = None
    zone: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

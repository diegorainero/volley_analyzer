from __future__ import annotations

import json
from pathlib import Path

DEFAULT_FIELD_POINTS = [[100, 100], [1820, 100], [1820, 900], [100, 900]]


class AppConfig:
    def __init__(self, path: str | Path = "config/field_calibration.json") -> None:
        self.path = Path(path)
        self.preferences_path = self.path.parent / "app_preferences.json"

    def load_field_points(self) -> list[list[float]]:
        if not self.path.exists():
            return DEFAULT_FIELD_POINTS

        data = json.loads(self.path.read_text(encoding="utf-8"))
        points = data.get("field_points") or DEFAULT_FIELD_POINTS
        if len(points) != 4:
            return DEFAULT_FIELD_POINTS
        return [[float(x), float(y)] for x, y in points]

    def load_num_fields(self) -> int:
        """Carica il numero di campi salvato (default 1)."""
        if not self.path.exists():
            return 1
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            num_fields = data.get("num_fields", 1)
            return max(1, min(2, num_fields))  # Assicura 1 o 2
        except Exception:
            return 1

    def save_field_points(self, points: list[list[float]], num_fields: int = 1) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"field_points": points, "num_fields": num_fields}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return self.path

    def load_preferences(self) -> dict:
        if not self.preferences_path.exists():
            return {}
        try:
            return json.loads(self.preferences_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_preferences(self, preferences: dict) -> Path:
        self.preferences_path.parent.mkdir(parents=True, exist_ok=True)
        self.preferences_path.write_text(
            json.dumps(preferences, indent=2), encoding="utf-8"
        )
        return self.preferences_path

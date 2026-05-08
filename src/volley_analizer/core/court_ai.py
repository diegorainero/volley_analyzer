from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover
    YOLO = None


class CourtKeypointDetector:
    """Rilevatore sperimentale dei 4 angoli campo tramite modello YOLO keypoints.

    Richiede un modello custom addestrato a restituire almeno 4 keypoint ordinati:
    alto-sinistra, alto-destra, basso-destra, basso-sinistra.
    """

    def __init__(self, model_path: str | Path):
        if YOLO is None:
            raise RuntimeError("Ultralytics non disponibile: installa ultralytics")
        self.model = YOLO(str(model_path))

    def detect_field_points(
        self, frame: np.ndarray, conf: float = 0.25
    ) -> list[list[float]] | None:
        results = self.model.predict(frame, verbose=False, conf=conf)
        if not results:
            return None
        result = results[0]
        keypoints = getattr(result, "keypoints", None)
        if keypoints is None or keypoints.xy is None or len(keypoints.xy) == 0:
            return None

        points = keypoints.xy[0].cpu().numpy().tolist()
        if len(points) < 4:
            return None
        return [[float(x), float(y)] for x, y in points[:4]]

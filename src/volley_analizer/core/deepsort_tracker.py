from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deep_sort_realtime.deepsort_tracker import DeepSort

from volley_analizer.core.types import Detection, Track


class DeepSortTracker:
    """Adapter DeepSORT compatibile con la pipeline esistente.

    La pipeline passa detections come oggetti `Detection` e si aspetta in output
    oggetti `Track`. `deep_sort_realtime`, invece, vuole detection in formato:
    `([left, top, width, height], confidence, class_name)`.
    """

    def __init__(
        self, max_age: int = 30, n_init: int = 3, nms_max_overlap: float = 1.0
    ):
        self.tracker = DeepSort(
            max_age=max_age,
            n_init=n_init,
            nms_max_overlap=nms_max_overlap,
        )

    def update(
        self, frame_or_shape, detections: list[Detection] | None = None
    ) -> list[Track]:
        # Compatibilità: supporta sia update(frame, detections) sia update(detections, frame)
        if isinstance(frame_or_shape, list):
            raw_detections = frame_or_shape
            frame = detections
        else:
            raw_detections = detections or []
            frame = None if isinstance(frame_or_shape, tuple) else frame_or_shape

        deep_sort_detections = []
        valid_detections: list[Detection] = []
        for det in raw_detections:
            if isinstance(det, dict):
                bbox = det.get("bbox")
                confidence = float(det.get("conf", det.get("confidence", 0.0)))
                class_name = str(det.get("cls", det.get("class_name", "player")))
            else:
                bbox = getattr(det, "bbox", None)
                confidence = float(getattr(det, "confidence", 0.0))
                class_name = getattr(det, "class_name", "player") or "player"

            if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
                print(
                    f"[DEBUG] Detection bbox malformata prima di DeepSORT: {bbox} "
                    f"(type: {type(bbox)})"
                )
                continue

            x1, y1, x2, y2 = [float(v) for v in bbox]
            width = max(0.0, x2 - x1)
            height = max(0.0, y2 - y1)
            if width <= 0 or height <= 0:
                print(f"[DEBUG] Detection bbox con dimensioni non valide: {bbox}")
                continue

            deep_sort_detections.append(
                ([x1, y1, width, height], confidence, class_name)
            )
            valid_detections.append(det)

        if not deep_sort_detections:
            return []

        tracks = self.tracker.update_tracks(deep_sort_detections, frame=frame)
        results: list[Track] = []
        for deep_track in tracks:
            if not deep_track.is_confirmed():
                continue

            try:
                x1, y1, x2, y2 = deep_track.to_ltrb()
            except Exception as exc:
                print(f"[DEBUG] Impossibile leggere bbox DeepSORT: {exc}")
                continue

            bbox = (float(x1), float(y1), float(x2), float(y2))
            matched_detection = self._match_detection_by_iou(bbox, valid_detections)
            if isinstance(matched_detection, dict):
                team_id = matched_detection.get("team_id")
                confidence = float(
                    matched_detection.get(
                        "conf", matched_detection.get("confidence", 1.0)
                    )
                )
            else:
                team_id = (
                    getattr(matched_detection, "team_id", None)
                    if matched_detection
                    else None
                )
                confidence = (
                    float(getattr(matched_detection, "confidence", 1.0))
                    if matched_detection
                    else 1.0
                )

            track = Track(
                track_id=int(deep_track.track_id),
                bbox=bbox,
                confidence=confidence,
                team_id=team_id,
            )
            if matched_detection is not None:
                matched_mask = (
                    matched_detection.get("mask")
                    if isinstance(matched_detection, dict)
                    else getattr(matched_detection, "mask", None)
                )
                if matched_mask is not None:
                    track.metadata["mask"] = matched_mask
            results.append(track)

        return results

    def _match_detection_by_iou(
        self, bbox: tuple[float, float, float, float], detections: list[Detection]
    ) -> Detection | None:
        best_detection = None
        best_iou = 0.0
        for det in detections:
            det_bbox = det.get("bbox") if isinstance(det, dict) else det.bbox
            iou = self._bbox_iou(bbox, det_bbox)
            if iou > best_iou:
                best_iou = iou
                best_detection = det
        return best_detection

    @staticmethod
    def _bbox_iou(
        a: tuple[float, float, float, float], b: tuple[float, float, float, float]
    ) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - inter_area
        if union <= 0:
            return 0.0
        return inter_area / union

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from ..core.analytics import AnalyticsEngine
from ..core.config import AppConfig
from ..core.detector import PlayerDetector
from ..core.field_mapper import FieldMapper
from ..core.video_processor import VideoProcessor


@dataclass(slots=True)
class PipelineConfig:
    video_path: str | int
    output_dir: str = "output"
    sample_every_n_frames: int = 3
    detector_model: str = "yolov8n.pt"
    detector_confidence: float = 0.25
    field_points: list[list[float]] | None = None
    detector_type: str = "yolo"
    num_fields: int = 1
    use_hw_accel: bool = True
    use_instance_segmentation: bool = False
    jersey_classifier_model: str | None = None
    jersey_confidence_threshold: float = 0.45


class VolleyballAnalysisPipeline:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.video = VideoProcessor(
            config.video_path,
            sample_every_n_frames=config.sample_every_n_frames,
            use_hw_accel=config.use_hw_accel,
        )

        # Usa YOLOv8-seg se richiesto esplicitamente o se il modello fornito è un modello segment.
        detector_model = config.detector_model
        detector_type = config.detector_type
        self.instance_segmentation_enabled = (
            config.use_instance_segmentation or "-seg" in detector_model
        )
        if self.instance_segmentation_enabled:
            detector_type = "yolo"
            if not detector_model:
                detector_model = "yolov8n-seg.pt"
            print(f"[INFO] Segmentazione instance attiva: {detector_model}")

        # Usa parametri consigliati per il tipo di detector
        recommended = PlayerDetector.get_recommended_config(detector_type)

        self.detector = PlayerDetector(
            model_name=detector_model,
            confidence_threshold=config.detector_confidence
            or recommended["confidence_threshold"],
            detector_type=detector_type,
            nms_threshold=recommended.get("nms_threshold", 0.45),
            soft_nms_enabled=recommended.get("soft_nms_enabled", True),
            soft_nms_method=recommended.get("soft_nms_method", "gaussian"),
            min_detection_area=recommended.get("min_detection_area", 500),
            aspect_ratio_min=recommended.get("aspect_ratio_min", 1.0),
            aspect_ratio_max=recommended.get("aspect_ratio_max", 4.0),
        )
        from ..core.deepsort_tracker import DeepSortTracker

        print("[INFO] Tracking abilitato: DeepSORT (deep_sort_realtime)")
        self.tracker = DeepSortTracker()
        calibration_points = config.field_points or AppConfig().load_field_points()
        num_fields = config.num_fields or AppConfig().load_num_fields()
        self.mapper = FieldMapper(src_points=calibration_points, num_fields=num_fields)
        self.analytics = AnalyticsEngine()
        self.jersey_classifier = None
        if config.jersey_classifier_model:
            try:
                from ..core.jersey_classifier import JerseyClassifier

                self.jersey_classifier = JerseyClassifier(
                    config.jersey_classifier_model
                )
                print(
                    f"[INFO] Classificatore maglia attivo: {config.jersey_classifier_model}"
                )
            except Exception as exc:
                print(f"[WARN] Classificatore maglia non disponibile: {exc}")
                self.jersey_classifier = None

        # Precompute field ROI (bounding rectangle of calibration points) to crop frames
        try:
            pts = calibration_points
            xs = [int(p[0]) for p in pts]
            ys = [int(p[1]) for p in pts]
            x_min = max(0, min(xs))
            y_min = max(0, min(ys))
            x_max = min(int(self.video.metadata.width), max(xs))
            y_max = min(int(self.video.metadata.height), max(ys))
            # Validate ROI
            if x_max > x_min and y_max > y_min:
                self.field_roi = (x_min, y_min, x_max, y_max)
            else:
                self.field_roi = None
        except Exception:
            self.field_roi = None

    def run(
        self, progress_callback: Callable[[dict], None] | None = None
    ) -> dict[str, Path]:
        processed_frames = 0
        total_processed = (
            max(1, self.video.metadata.frame_count // self.config.sample_every_n_frames)
            if self.video.metadata.frame_count
            else 1
        )

        for frame_idx, timestamp, frame in self.video.frames():
            # Crop to field ROI to avoid detecting spectators/outside objects
            crop_frame = frame
            offset_x = 0
            offset_y = 0
            if hasattr(self, "field_roi") and self.field_roi is not None:
                x_min, y_min, x_max, y_max = self.field_roi
                try:
                    crop_frame = frame[y_min:y_max, x_min:x_max]
                    offset_x, offset_y = x_min, y_min
                except Exception:
                    crop_frame = frame
                    offset_x, offset_y = 0, 0

            detections = self.detector.detect(crop_frame)
            detections = self._prepare_detections_for_full_frame(
                detections,
                frame_shape=frame.shape,
                roi_shape=crop_frame.shape,
                offset_x=offset_x,
                offset_y=offset_y,
            )

            # Filtra detections fuori dal campo (basato sulla calibrazione)
            detections_in_field = self._filter_detections_in_field(detections)
            tracks = self.tracker.update(frame, detections_in_field)
            for track in tracks:
                self._classify_track_jersey(frame, track)
                field_position = self.mapper.map_bbox_to_field(track.bbox)
                zone = self.mapper.get_zone(field_position)
                track.field_position = field_position
                track.zone = zone
                self.analytics.update(frame_idx, timestamp, track)

            processed_frames += 1

            if progress_callback is not None:
                preview = self._build_preview_frame(frame, tracks)
                progress_callback(
                    {
                        "frame_idx": frame_idx,
                        "timestamp": timestamp,
                        "processed_frames": processed_frames,
                        "total_processed_frames": total_processed,
                        "detections": len(detections),
                        "tracks": len(tracks),
                        "preview_frame": preview,
                    }
                )

        self.video.release()
        return self.analytics.export(self.config.output_dir)

    def run_chunked(
        self,
        chunk_seconds=60,
        progress_callback: Callable[[dict], None] | None = None,
        stop_callback: Callable[[], bool] | None = None,
    ) -> dict[str, Path]:
        processed_frames = 0
        total_processed = (
            max(1, self.video.metadata.frame_count // self.config.sample_every_n_frames)
            if self.video.metadata.frame_count
            else 1
        )
        fps = self.video.metadata.fps or 25
        frames_per_chunk = int(fps * chunk_seconds)
        chunk = []
        stopped = False

        for frame_idx, timestamp, frame in self.video.frames():
            if stop_callback and stop_callback():
                stopped = True
                break
            chunk.append((frame_idx, timestamp, frame))
            if len(chunk) >= frames_per_chunk:
                stopped = self._process_chunk(
                    chunk,
                    progress_callback,
                    processed_frames,
                    total_processed,
                    stop_callback,
                )
                processed_frames += len(chunk)
                chunk = []
                if stopped:
                    break

        if chunk and not stopped:
            self._process_chunk(
                chunk,
                progress_callback,
                processed_frames,
                total_processed,
                stop_callback,
            )

        self.video.release()
        return self.analytics.export(self.config.output_dir)

    def _process_chunk(
        self,
        chunk,
        progress_callback,
        processed_frames,
        total_processed,
        stop_callback=None,
    ) -> bool:
        for frame_idx, timestamp, frame in chunk:
            if stop_callback and stop_callback():
                return True
            # Crop to field ROI to avoid detecting spectators/outside objects
            crop_frame = frame
            offset_x = 0
            offset_y = 0
            if hasattr(self, "field_roi") and self.field_roi is not None:
                x_min, y_min, x_max, y_max = self.field_roi
                try:
                    crop_frame = frame[y_min:y_max, x_min:x_max]
                    offset_x, offset_y = x_min, y_min
                except Exception:
                    crop_frame = frame
                    offset_x, offset_y = 0, 0

            detections = self.detector.detect(crop_frame)
            detections = self._prepare_detections_for_full_frame(
                detections,
                frame_shape=frame.shape,
                roi_shape=crop_frame.shape,
                offset_x=offset_x,
                offset_y=offset_y,
            )

            # Filtra detections fuori dal campo (basato sulla calibrazione)
            detections_in_field = self._filter_detections_in_field(detections)
            tracks = self.tracker.update(frame, detections_in_field)
            for track in tracks:
                self._classify_track_jersey(frame, track)
                field_position = self.mapper.map_bbox_to_field(track.bbox)
                zone = self.mapper.get_zone(field_position)
                track.field_position = field_position
                track.zone = zone
                self.analytics.update(frame_idx, timestamp, track)
            if progress_callback is not None:
                preview = self._build_preview_frame(frame, tracks)
                progress_callback(
                    {
                        "frame_idx": frame_idx,
                        "timestamp": timestamp,
                        "processed_frames": processed_frames + 1,
                        "total_processed_frames": total_processed,
                        "detections": len(detections),
                        "tracks": len(tracks),
                        "preview_frame": preview,
                    }
                )
        return False

    def _classify_track_jersey(self, frame, track) -> None:
        if self.jersey_classifier is None:
            return
        try:
            x1, y1, x2, y2 = [int(round(v)) for v in track.bbox]
            h, w = frame.shape[:2]
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w, x2))
            y2 = max(0, min(h, y2))
            if x2 <= x1 or y2 <= y1:
                return
            crop = frame[y1:y2, x1:x2]
            label, confidence = self.jersey_classifier.predict(crop)
            track.metadata["jersey_classifier_label"] = label
            track.metadata["jersey_classifier_confidence"] = confidence
            if confidence >= self.config.jersey_confidence_threshold:
                if label.startswith("team_"):
                    track.team_id = label
                else:
                    track.jersey_number = label
        except Exception as exc:
            print(f"[DEBUG] Errore classificatore maglia: {exc}")

    def _prepare_detections_for_full_frame(
        self,
        detections: list,
        frame_shape: tuple[int, int, int],
        roi_shape: tuple[int, int, int],
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> list:
        """Porta bbox e maschere dalla ROI al frame completo.

        YOLOv8-seg restituisce maschere riferite all'immagine passata al detector.
        Se analizziamo una ROI del campo, qui convertiamo le maschere in maschere
        full-frame, così preview e matching restano coerenti con le bbox originali.
        """
        frame_h, frame_w = frame_shape[:2]
        roi_h, roi_w = roi_shape[:2]

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            det.bbox = (
                float(x1 + offset_x),
                float(y1 + offset_y),
                float(x2 + offset_x),
                float(y2 + offset_y),
            )

            mask = getattr(det, "mask", None)
            if mask is None:
                continue

            try:
                mask_uint8 = (mask.astype(float) > 0.5).astype("uint8")
                if mask_uint8.shape[:2] != (roi_h, roi_w):
                    mask_uint8 = cv2.resize(
                        mask_uint8,
                        (roi_w, roi_h),
                        interpolation=cv2.INTER_NEAREST,
                    )

                full_mask = np.zeros((frame_h, frame_w), dtype=bool)
                y_end = min(frame_h, offset_y + roi_h)
                x_end = min(frame_w, offset_x + roi_w)
                full_mask[offset_y:y_end, offset_x:x_end] = mask_uint8[
                    : y_end - offset_y,
                    : x_end - offset_x,
                ].astype(bool)
                det.mask = full_mask
            except Exception as exc:
                print(f"[DEBUG] Impossibile normalizzare maschera segmentation: {exc}")
                det.mask = None

        return detections

    def _filter_detections_in_field(self, detections: list) -> list:
        """Filtra detections il cui punto di appoggio (foot) non si mappa dentro il campo calibrato."""
        if not detections:
            return detections
        if not hasattr(self, "mapper") or self.mapper is None:
            return detections

        filtered = []
        for det in detections:
            try:
                x_m, y_m = self.mapper.map_bbox_to_field(det.bbox)
            except Exception:
                # Se la mappatura fallisce, manteniamo la detection per non perdere dati
                filtered.append(det)
                continue

            # Controlla se il punto mappato è dentro i limiti del campo
            if 0 <= x_m <= self.mapper.field.width_m and 0 <= y_m <= (
                self.mapper.field.height_m * self.mapper.num_fields
            ):
                filtered.append(det)

        return filtered

    def _build_preview_frame(self, frame, tracks):
        preview = frame.copy()
        self._draw_field_zone_overlay(preview)
        # Visualizza maschere se disponibili
        for track in tracks:
            mask = getattr(track, "mask", None)
            if mask is None and getattr(track, "metadata", None):
                mask = track.metadata.get("mask")
            if mask is not None:
                try:
                    mask_bool = mask.astype(bool)
                    if mask_bool.shape[:2] != preview.shape[:2]:
                        mask_bool = cv2.resize(
                            mask_bool.astype("uint8"),
                            (preview.shape[1], preview.shape[0]),
                            interpolation=cv2.INTER_NEAREST,
                        ).astype(bool)
                    color_overlay = np.zeros_like(preview)
                    color_overlay[mask_bool] = (0, 140, 255)
                    blended = cv2.addWeighted(preview, 0.65, color_overlay, 0.35, 0)
                    preview[mask_bool] = blended[mask_bool]
                except Exception as exc:
                    print(f"[DEBUG] Impossibile disegnare maschera segmentation: {exc}")
            # Debug: controlla il tipo e il valore di bbox
            bbox = getattr(track, "bbox", None)
            if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
                print(
                    f"[DEBUG] bbox malformato per track_id={getattr(track, 'track_id', None)}: {bbox} (type: {type(bbox)})"
                )
                continue
            x1, y1, x2, y2 = map(int, bbox)
            color = (0, 255, 0) if track.team_id == "team_green" else (255, 0, 0)
            if track.team_id == "team_red":
                color = (0, 0, 255)
            elif track.team_id == "team_yellow":
                color = (0, 255, 255)
            elif track.team_id == "team_blue":
                color = (255, 0, 0)

            cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
            label = f"ID {track.track_id}"
            if track.jersey_number:
                label += f" #{track.jersey_number}"
            if track.zone is not None:
                label += f" Z{track.zone}"
            cv2.putText(
                preview,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        return preview

    def _draw_field_zone_overlay(self, preview) -> None:
        try:
            total_h = self.mapper.field.height_m * self.mapper.num_fields
            # Bordo campo
            corners = [
                self.mapper.map_field_to_image((0, 0)),
                self.mapper.map_field_to_image((self.mapper.field.width_m, 0)),
                self.mapper.map_field_to_image((self.mapper.field.width_m, total_h)),
                self.mapper.map_field_to_image((0, total_h)),
            ]
            pts = np.array(corners, dtype=np.int32)
            cv2.polylines(preview, [pts], isClosed=True, color=(0, 0, 0), thickness=2)

            # Linee colonne
            for x_m in (3.0, 6.0):
                p1 = self.mapper.map_field_to_image((x_m, 0))
                p2 = self.mapper.map_field_to_image((x_m, total_h))
                cv2.line(preview, p1, p2, (60, 60, 60), 1)

            # Linee righe e rete
            row_lines = [4.5]
            if self.mapper.num_fields == 2:
                row_lines = [4.5, 9.0, 13.5]
            for y_m in row_lines:
                p1 = self.mapper.map_field_to_image((0, y_m))
                p2 = self.mapper.map_field_to_image((self.mapper.field.width_m, y_m))
                color = (0, 0, 255) if abs(y_m - 9.0) < 0.01 else (60, 60, 60)
                thickness = 3 if abs(y_m - 9.0) < 0.01 else 1
                cv2.line(preview, p1, p2, color, thickness)

            if self.mapper.num_fields == 2:
                zone_layout = [
                    ([1, 6, 5], 0.0),
                    ([2, 3, 4], 4.5),
                    ([4, 3, 2], 9.0),
                    ([5, 6, 1], 13.5),
                ]
            else:
                zone_layout = [
                    ([4, 3, 2], 0.0),
                    ([5, 6, 1], 4.5),
                ]

            for zones, y_start in zone_layout:
                for col, zone in enumerate(zones):
                    center = self.mapper.map_field_to_image(
                        (col * 3.0 + 1.5, y_start + 2.25)
                    )
                    cv2.putText(
                        preview,
                        str(zone),
                        center,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (80, 40, 40),
                        2,
                    )
        except Exception:
            return

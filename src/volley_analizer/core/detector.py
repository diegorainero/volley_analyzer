from __future__ import annotations

from collections import Counter

import cv2
import numpy as np

from .team_classifier import TeamClassifier, TeamColorProfile
from .types import Detection

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover
    YOLO = None


class PlayerDetector:
    """
    Advanced player detector with improved filtering and deduplication.

    Features:
    - Adaptive confidence thresholding based on frame statistics
    - Non-Maximum Suppression (NMS) for duplicate detection removal
    - Soft-NMS for handling nearby players
    - Aspect ratio filtering for human-like proportions
    - Minimum size filtering for consistency
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence_threshold: float = 0.25,
        detector_type: str = "yolo",
        nms_threshold: float = 0.45,
        soft_nms_enabled: bool = True,
        soft_nms_method: str = "linear",  # "linear", "gaussian", "hard"
        aspect_ratio_min: float = 1.0,
        aspect_ratio_max: float = 4.0,
        min_detection_area: int = 500,
        max_detection_area: int | None = None,
        adaptive_confidence: bool = True,
        team_profiles: dict[str, TeamColorProfile] | None = None,
        use_team_classifier: bool = True,
    ) -> None:
        """
        Initialize PlayerDetector with advanced filtering options.

        Args:
            model_name: Path to YOLO model weights
            confidence_threshold: Base confidence threshold for detections
            detector_type: "yolo" or "hog"
            nms_threshold: IoU threshold for NMS (hard suppression)
            soft_nms_enabled: Enable Soft-NMS for nearby detections
            soft_nms_method: Method for Soft-NMS ("linear", "gaussian", "hard")
            aspect_ratio_min: Minimum height/width ratio for players
            aspect_ratio_max: Maximum height/width ratio for players
            min_detection_area: Minimum bounding box area in pixels
            max_detection_area: Maximum bounding box area (None for unlimited)
            adaptive_confidence: Enable adaptive thresholding based on frame stats
            team_profiles: Dictionary con profili di colore per squadra
            use_team_classifier: Abilita il nuovo classificatore di squadra
        """
        self.confidence_threshold = confidence_threshold
        self.model_name = model_name
        self.detector_type = detector_type
        self.model = None
        self.debug = False  # Flag per debug

        # NMS parameters
        self.nms_threshold = nms_threshold
        self.soft_nms_enabled = soft_nms_enabled
        self.soft_nms_method = soft_nms_method

        # Filtering parameters
        self.aspect_ratio_min = aspect_ratio_min
        self.aspect_ratio_max = aspect_ratio_max
        self.min_detection_area = min_detection_area
        self.max_detection_area = max_detection_area
        self.adaptive_confidence = adaptive_confidence

        # Calibration data for confidence
        self.confidence_history = []
        self.max_history_size = 100

        if detector_type == "yolo":
            try:
                from ultralytics import YOLO

                self.model = YOLO(model_name)
                # Log automatico se modello -seg
                if (
                    hasattr(self.model, "task")
                    and getattr(self.model, "task", None) == "segment"
                ):
                    print("[INFO] Segmentazione instance attiva: modello YOLOv8-seg")
                elif "-seg" in model_name:
                    print("[INFO] Segmentazione instance attiva: modello YOLOv8-seg")
            except Exception as e:
                print(f"YOLO non disponibile: {e}")
                self.model = None

        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        # Background subtractor per HOG (migliora rilevamento in movimento)
        self.bg_subtractor = None
        if detector_type == "hog":
            try:
                # history e varThreshold possono essere aggiustati in base al video
                self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                    history=500, varThreshold=16, detectShadows=False
                )
            except Exception:
                self.bg_subtractor = None

        # Inizializza il classificatore di squadra
        self.use_team_classifier = use_team_classifier
        if use_team_classifier:
            self.team_classifier = TeamClassifier(team_profiles=team_profiles)
        else:
            self.team_classifier = None

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """
        Detect players in frame with advanced filtering.

        Args:
            frame: Input frame (BGR image)

        Returns:
            List of filtered Detection objects
        """
        if self.debug:
            print(
                f"[DETECT DEBUG] Chiamato detect con detector_type={self.detector_type}, conf={self.confidence_threshold}, model={self.model_name}"
            )
        if self.detector_type == "yolo" and self.model is not None:
            return self._detect_with_yolo(frame)
        return self._detect_with_hog(frame)

    @staticmethod
    def get_recommended_config(detector_type: str = "yolo") -> dict:
        """Ritorna configurazione consigliata per il tipo di detector.

        Args:
            detector_type: "yolo" o "hog"

        Returns:
            Dict con parametri ottimizzati
        """
        if detector_type == "hog":
            # HOG è meno accurato, quindi filtri più permissivi
            return {
                "confidence_threshold": 0.05,  # Molto permissivo
                "min_detection_area": 150,  # Più piccolo (default 500)
                "aspect_ratio_min": 1.0,  # Valori realistici per persone verticali
                "aspect_ratio_max": 4.0,  # Permette persone molto 'alte' in bounding box
                "nms_threshold": 0.5,
                "soft_nms_enabled": True,
                "soft_nms_method": "gaussian",
            }
        else:  # yolo
            # YOLO è più accurato, filtri più stretti
            return {
                "confidence_threshold": 0.25,  # Valore più bilanciato
                "min_detection_area": 300,  # Medio
                "aspect_ratio_min": 1.0,  # Valori realistici per persone verticali
                "aspect_ratio_max": 4.0,
                "nms_threshold": 0.45,
                "soft_nms_enabled": True,
                "soft_nms_method": "gaussian",
            }

    def enable_debug(self, enabled: bool = True) -> None:
        """Abilita/disabilita il debug output."""
        self.debug = enabled

    def _detect_with_yolo(self, frame: np.ndarray) -> list[Detection]:
        """Detect with YOLO and apply advanced filtering."""
        # Adaptive confidence threshold based on frame statistics
        conf_threshold = self._get_adaptive_confidence_threshold(frame)

        # Forza filtro solo persone (classe 0 COCO)
        results = self.model.predict(
            frame, verbose=False, classes=[0], conf=conf_threshold
        )
        detections: list[Detection] = []
        raw_count = 0

        for i, box in enumerate(results[0].boxes):
            raw_count += 1
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])

            # Initialize mask (if segmentation model provided masks)
            mask = None
            try:
                masks = getattr(results[0], "masks", None)
                if masks is not None:
                    data = getattr(masks, "data", None)
                    if data is None:
                        data = getattr(masks, "masks", None)
                    if data is not None and len(data) > i:
                        m = data[i]
                        try:
                            # torch tensor
                            import torch

                            if isinstance(m, torch.Tensor):
                                mask = m.cpu().numpy()
                            else:
                                mask = np.array(m)
                        except Exception:
                            mask = np.array(m)
                        # ensure boolean
                        try:
                            mask = mask.astype(bool)
                        except Exception:
                            pass
            except Exception:
                mask = None

            bbox = (float(x1), float(y1), float(x2), float(y2))

            # If mask exists and covers area, optionally refine bbox to mask bounds.
            # Usiamo il bbox della maschera solo se la maschera ha le stesse dimensioni
            # del frame di inferenza; altrimenti teniamo il bbox YOLO, che è già in
            # coordinate frame corrette.
            if mask is not None and mask.size and mask.shape[:2] == frame.shape[:2]:
                try:
                    ys, xs = np.where(mask)
                    if ys.size > 0 and xs.size > 0:
                        mx1, my1 = float(xs.min()), float(ys.min())
                        mx2, my2 = float(xs.max()), float(ys.max())
                        # Only use mask bbox if it has reasonable area
                        if (mx2 - mx1) * (my2 - my1) > 20:
                            bbox = (mx1, my1, mx2, my2)
                except Exception:
                    pass

            # Apply filtering
            if not self._passes_size_filter(bbox):
                if self.debug:
                    print(f"  YOLO: Scartato per size: {bbox}")
                continue
            if not self._passes_aspect_ratio_filter(bbox):
                if self.debug:
                    print(f"  YOLO: Scartato per aspect ratio: {bbox}")
                continue

            crop = frame[
                int(max(0, bbox[1])) : int(max(0, bbox[3])),
                int(max(0, bbox[0])) : int(max(0, bbox[2])),
            ]

            # Verifica che il crop non sia vuoto
            if crop.size == 0:
                team_id = "unknown"
            # Classifica il team usando il nuovo classificatore
            elif self.use_team_classifier and self.team_classifier is not None:
                try:
                    team_id, _ = self.team_classifier.classify(crop)
                except Exception:
                    team_id = self._infer_team_from_crop(crop)
            else:
                team_id = self._infer_team_from_crop(crop)

            if self.debug:
                print(
                    f"  YOLO: Detection accettata: conf={confidence:.3f}, team={team_id}"
                )

            detections.append(
                Detection(bbox=bbox, confidence=confidence, team_id=team_id, mask=mask)
            )

        if self.debug:
            print(f"[YOLO] Raw: {raw_count}, After filter: {len(detections)}")

        # Apply post-processing filters
        detections = self._apply_nms(detections)
        detections = self._merge_nearby_boxes(detections)

        # Update confidence history for calibration
        self._update_confidence_history([d.confidence for d in detections])

        return detections

    def _detect_with_hog(self, frame: np.ndarray) -> list[Detection]:
        """Detect with HOG and apply advanced filtering."""
        conf_threshold = self._get_adaptive_confidence_threshold(frame)

        # Ridimensiona il frame per aumentare la probabilità di detection
        frame_resized = cv2.resize(frame, (640, 480))
        scale_x = frame.shape[1] / 640
        scale_y = frame.shape[0] / 480

        # HOG detections
        rects, weights = self.hog.detectMultiScale(
            frame_resized, winStride=(4, 4), padding=(8, 8), scale=1.02, hitThreshold=0
        )

        # Normalize outputs
        rects_list = []
        weights_list = []
        try:
            if isinstance(rects, np.ndarray) and rects.size:
                rects_list = [tuple(map(int, r)) for r in rects]
        except Exception:
            rects_list = []

        try:
            if weights is not None:
                weights_arr = np.array(weights).reshape(-1)
                weights_list = [float(w) for w in weights_arr]
        except Exception:
            weights_list = []

        detections: list[Detection] = []
        raw_count = len(rects_list)

        # Add foreground regions from bg_subtractor to improve HOG
        fg_candidates = []
        if self.bg_subtractor is not None:
            try:
                fgmask = self.bg_subtractor.apply(frame_resized)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel, iterations=1)
                fgmask = cv2.dilate(fgmask, kernel, iterations=2)
                contours, _ = cv2.findContours(
                    fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area < 500:
                        continue
                    x, y, w, h = cv2.boundingRect(cnt)
                    pad = 10
                    x = max(0, x - pad)
                    y = max(0, y - pad)
                    w = min(frame_resized.shape[1] - x, w + 2 * pad)
                    h = min(frame_resized.shape[0] - y, h + 2 * pad)
                    fg_candidates.append((x, y, w, h))
            except Exception:
                fg_candidates = []

        # Combine HOG rects and FG candidates
        combined = []
        for i, r in enumerate(rects_list):
            x, y, w, h = r
            conf = weights_list[i] if i < len(weights_list) else 0.6
            combined.append((x, y, w, h, conf))
        for r in fg_candidates:
            x, y, w, h = r
            combined.append((x, y, w, h, 0.6))

        for x, y, w, h, confidence in combined:
            if confidence < conf_threshold:
                if self.debug:
                    print(
                        f"  HOG: Scartato per confidence: {confidence:.3f} < {conf_threshold:.3f}"
                    )
                continue

            # Scala indietro le coordinate al frame originale
            x1_orig = int(x * scale_x)
            y1_orig = int(y * scale_y)
            x2_orig = int((x + w) * scale_x)
            y2_orig = int((y + h) * scale_y)

            bbox = (float(x1_orig), float(y1_orig), float(x2_orig), float(y2_orig))

            # Apply filtering
            if not self._passes_size_filter(bbox):
                if self.debug:
                    print(f"  HOG: Scartato per size: {bbox}")
                continue
            if not self._passes_aspect_ratio_filter(bbox):
                if self.debug:
                    print(f"  HOG: Scartato per aspect ratio: {bbox}")
                continue

            crop = frame[y1_orig:y2_orig, x1_orig:x2_orig]

            if crop.size == 0:
                team_id = "unknown"
            elif self.use_team_classifier and self.team_classifier is not None:
                try:
                    team_id, _ = self.team_classifier.classify(crop)
                except Exception:
                    team_id = self._infer_team_from_crop(crop)
            else:
                team_id = self._infer_team_from_crop(crop)

            if self.debug:
                print(
                    f"  HOG: Detection accettata: conf={confidence:.3f}, team={team_id}"
                )

            detections.append(
                Detection(bbox=bbox, confidence=confidence, team_id=team_id)
            )

        if self.debug:
            print(f"[HOG] Raw: {raw_count}, After filter: {len(detections)}")

        detections = self._apply_nms(detections)
        detections = self._merge_nearby_boxes(detections)

        self._update_confidence_history([d.confidence for d in detections])

        return detections

    def _passes_size_filter(self, bbox: tuple[float, float, float, float]) -> bool:
        """
        Check if detection passes minimum and maximum size constraints.

        Args:
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            True if detection passes size filter
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height

        if area < self.min_detection_area:
            return False

        if self.max_detection_area is not None and area > self.max_detection_area:
            return False

        return True

    def _passes_aspect_ratio_filter(
        self, bbox: tuple[float, float, float, float]
    ) -> bool:
        """
        Check if detection has human-like aspect ratio (height/width).

        Args:
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            True if aspect ratio is within acceptable range
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1

        if width == 0:
            return False

        aspect_ratio = height / width

        return self.aspect_ratio_min <= aspect_ratio <= self.aspect_ratio_max

    def _apply_nms(self, detections: list[Detection]) -> list[Detection]:
        """
        Apply Non-Maximum Suppression and optionally Soft-NMS.

        Args:
            detections: List of detections to filter

        Returns:
            Filtered detections with duplicates removed
        """
        if not detections:
            return detections

        if self.soft_nms_enabled:
            return self._soft_nms(detections)
        else:
            return self._hard_nms(detections)

    def _hard_nms(self, detections: list[Detection]) -> list[Detection]:
        """
        Standard Hard-NMS: remove detections with high IoU overlap.

        Args:
            detections: List of detections

        Returns:
            Filtered detections
        """
        if not detections:
            return detections

        # Sort by confidence descending
        sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
        keep = []

        while sorted_dets:
            current = sorted_dets.pop(0)
            keep.append(current)

            # Remove detections with high IoU
            sorted_dets = [
                d
                for d in sorted_dets
                if self._compute_iou(current.bbox, d.bbox) < self.nms_threshold
            ]

        return keep

    def _soft_nms(self, detections: list[Detection]) -> list[Detection]:
        """
        Soft-NMS: reduce confidence of overlapping detections instead of removing.
        Supports linear, gaussian, and hard methods.

        Args:
            detections: List of detections

        Returns:
            Filtered detections with adjusted confidences
        """
        if not detections:
            return detections

        # Sort by confidence descending
        sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
        keep = []

        while sorted_dets:
            current = sorted_dets.pop(0)
            keep.append(current)

            # Adjust confidence of overlapping detections
            new_sorted = []
            for det in sorted_dets:
                iou = self._compute_iou(current.bbox, det.bbox)

                if iou > self.nms_threshold:
                    # Apply Soft-NMS method
                    if self.soft_nms_method == "linear":
                        det.confidence *= 1 - iou
                    elif self.soft_nms_method == "gaussian":
                        det.confidence *= np.exp(-(iou**2) / 0.5)
                    # "hard" method removes it (like standard NMS)
                    else:
                        continue

                new_sorted.append(det)

            sorted_dets = new_sorted

        # Filter out low-confidence detections after Soft-NMS
        keep = [d for d in keep if d.confidence >= self.confidence_threshold]

        return keep

    def _merge_nearby_boxes(
        self, detections: list[Detection], merge_threshold: float = 0.5
    ) -> list[Detection]:
        """
        Merge nearby bounding boxes if overlap exceeds threshold.
        Useful for handling overlapping detections of nearby players.

        Args:
            detections: List of detections
            merge_threshold: IoU threshold for merging

        Returns:
            Merged detections
        """
        if not detections or len(detections) < 2:
            return detections

        merged = []
        used = set()

        for i, det1 in enumerate(detections):
            if i in used:
                continue

            bboxes_to_merge = [det1.bbox]
            confidences = [det1.confidence]
            team_ids = [det1.team_id]

            for j, det2 in enumerate(detections[i + 1 :], start=i + 1):
                if j in used:
                    continue

                if self._compute_iou(det1.bbox, det2.bbox) > merge_threshold:
                    bboxes_to_merge.append(det2.bbox)
                    confidences.append(det2.confidence)
                    team_ids.append(det2.team_id)
                    used.add(j)

            # Create merged detection
            if len(bboxes_to_merge) > 1:
                merged_bbox = self._merge_boxes(bboxes_to_merge)
                merged_confidence = float(np.mean(confidences))
                # Use most common team_id
                team_id = Counter(team_ids).most_common(1)[0][0]
            else:
                merged_bbox = det1.bbox
                merged_confidence = det1.confidence
                team_id = det1.team_id

            merged.append(
                Detection(
                    bbox=merged_bbox,
                    confidence=merged_confidence,
                    team_id=team_id,
                )
            )
            used.add(i)

        return merged

    @staticmethod
    def _merge_boxes(
        bboxes: list[tuple[float, float, float, float]],
    ) -> tuple[float, float, float, float]:
        """
        Merge multiple bounding boxes into one.

        Args:
            bboxes: List of bounding boxes (x1, y1, x2, y2)

        Returns:
            Merged bounding box
        """
        x1_vals = [bbox[0] for bbox in bboxes]
        y1_vals = [bbox[1] for bbox in bboxes]
        x2_vals = [bbox[2] for bbox in bboxes]
        y2_vals = [bbox[3] for bbox in bboxes]

        return (
            float(min(x1_vals)),
            float(min(y1_vals)),
            float(max(x2_vals)),
            float(max(y2_vals)),
        )

    @staticmethod
    def _compute_iou(
        bbox1: tuple[float, float, float, float],
        bbox2: tuple[float, float, float, float],
    ) -> float:
        """
        Compute Intersection over Union (IoU) between two bounding boxes.

        Args:
            bbox1: First bounding box (x1, y1, x2, y2)
            bbox2: Second bounding box (x1, y1, x2, y2)

        Returns:
            IoU value between 0 and 1
        """
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2

        # Intersection area
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)

        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0

        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)

        # Union area
        bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)
        bbox2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = bbox1_area + bbox2_area - inter_area

        if union_area == 0:
            return 0.0

        return inter_area / union_area

    def _get_adaptive_confidence_threshold(self, frame: np.ndarray) -> float:
        """
        Calculate adaptive confidence threshold based on frame statistics.

        Increases threshold for well-lit frames (low variance), decreases for
        poor conditions (high variance).

        Args:
            frame: Input frame

        Returns:
            Adjusted confidence threshold
        """
        if not self.adaptive_confidence:
            return self.confidence_threshold

        # Calculate frame brightness and variance
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray) / 255.0
        variance = np.var(gray) / 255.0

        # Adaptive adjustment
        # Low brightness or high variance -> lower threshold
        brightness_factor = brightness if brightness > 0.3 else 0.7
        variance_factor = 1.0 - min(variance, 0.3) / 0.3  # Factor between 0.7-1.0

        adjusted_threshold = (
            self.confidence_threshold * brightness_factor * variance_factor
        )

        return np.clip(
            adjusted_threshold,
            self.confidence_threshold * 0.5,
            self.confidence_threshold,
        )

    def _update_confidence_history(self, confidences: list[float]) -> None:
        """
        Update confidence history for calibration.

        Args:
            confidences: List of confidence values from recent detection
        """
        self.confidence_history.extend(confidences)
        if len(self.confidence_history) > self.max_history_size:
            self.confidence_history = self.confidence_history[-self.max_history_size :]

    def get_confidence_calibration(self) -> dict[str, float]:
        """
        Get confidence calibration statistics from detection history.

        Returns:
            Dictionary with mean, std, min, max confidence values
        """
        if not self.confidence_history:
            return {
                "mean": self.confidence_threshold,
                "std": 0.0,
                "min": self.confidence_threshold,
                "max": self.confidence_threshold,
            }

        confidences = np.array(self.confidence_history)

        return {
            "mean": float(np.mean(confidences)),
            "std": float(np.std(confidences)),
            "min": float(np.min(confidences)),
            "max": float(np.max(confidences)),
            "count": len(self.confidence_history),
        }

    @staticmethod
    def _infer_team_from_crop(crop: np.ndarray) -> str:
        """
        Infer team color from bounding box crop.

        Args:
            crop: Cropped image region

        Returns:
            Team ID string
        """
        if crop.size == 0:
            return "unknown"

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        h_channel = hsv[:, :, 0]
        dominant_hue = (
            Counter((h_channel.flatten() // 10).tolist()).most_common(1)[0][0] * 10
        )

        if dominant_hue < 15 or dominant_hue > 165:
            return "team_red"
        if 15 <= dominant_hue < 40:
            return "team_yellow"
        if 40 <= dominant_hue < 90:
            return "team_green"
        if 90 <= dominant_hue < 140:
            return "team_blue"
        return "unknown"

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .types import Detection, Track

try:
    from yolox.tracker.byte_tracker import BYTETracker
except Exception:  # pragma: no cover
    BYTETracker = None

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except Exception:  # pragma: no cover
    DeepSort = None


@dataclass(slots=True)
class _SimpleTrackState:
    track_id: int
    bbox: tuple[float, float, float, float]
    confidence: float
    team_id: str | None
    missed_frames: int = 0


class MultiObjectTracker:
    def __init__(
        self,
        fps: int = 25,
        distance_threshold: float = 90.0,
        max_missed_frames: int = 20,
    ) -> None:
        self.distance_threshold = distance_threshold
        self.max_missed_frames = max_missed_frames
        self.next_track_id = 1
        self.simple_tracks: list[_SimpleTrackState] = []
        self.byte_tracker = None
        self.debug = False

        if BYTETracker is not None:
            try:
                self.byte_tracker = BYTETracker(
                    track_thresh=0.25, track_buffer=30, match_thresh=0.8, frame_rate=fps
                )
                print("[TRACKER] BYTETracker inizializzato (using yolox)")
            except Exception as e:
                print(f"[TRACKER] Impossibile inizializzare BYTETracker: {e}")
                self.byte_tracker = None

        # Prova a inizializzare DeepSort come fallback (deep_sort_realtime)
        self.deep_sort = None
        if DeepSort is not None:
            try:
                self.deep_sort = DeepSort(max_age=self.max_missed_frames)
                print("[TRACKER] DeepSort inizializzato (deep_sort_realtime)")
            except Exception as e:
                print(f"[TRACKER] Impossibile inizializzare DeepSort: {e}")
                self.deep_sort = None

    def update(self, frame_or_shape, detections: list[Detection]) -> list[Track]:
        """Update tracker with detections.

        frame_or_shape may be either a numpy array frame or a tuple (height, width, channels).
        This method prefers BYTETracker (if available), then DeepSort, otherwise the internal simple tracker.
        """
        frame = None
        # Determine if frame_or_shape is an actual frame (numpy array) or a shape tuple
        if not isinstance(frame_or_shape, tuple):
            frame = frame_or_shape
            frame_shape = getattr(frame, "shape", None)
        else:
            frame_shape = frame_or_shape

        # Prefer BYTETracker if available
        if self.byte_tracker is not None and detections and np is not None:
            return self._update_bytetrack(frame_shape, detections)

        # Fallback to DeepSort if available
        if getattr(self, "deep_sort", None) is not None and detections:
            return self._update_deepsort(frame, detections)

        # Final fallback: simple tracker
        return self._update_simple(detections)

    def _update_bytetrack(
        self, frame_shape: tuple[int, int, int], detections: list[Detection]
    ) -> list[Track]:
        dets = np.array(
            [[*det.bbox, det.confidence] for det in detections], dtype=float
        )
        online_targets = self.byte_tracker.update(
            dets, [frame_shape[0], frame_shape[1]], [frame_shape[0], frame_shape[1]]
        )
        tracks: list[Track] = []

        for target in online_targets:
            x, y, w, h = target.tlwh
            bbox = (float(x), float(y), float(x + w), float(y + h))
            team_id = self._match_team_id(bbox, detections)
            tracks.append(
                Track(
                    track_id=int(target.track_id),
                    bbox=bbox,
                    confidence=1.0,
                    team_id=team_id,
                )
            )

        return tracks

    def _update_deepsort(
        self, frame: np.ndarray | None, detections: list[Detection]
    ) -> list[Track]:
        """Update using deep_sort_realtime if available. Returns list[Track].

        This function is defensive: it tries several possible DeepSort APIs and
        falls back to the simple tracker on error. If DeepSort complains that
        embeddings or frame are required, we compute a simple color-histogram
        embedding per detection and retry with several kwarg names.
        """
        # Prepare detections: list of [x1, y1, x2, y2, confidence]
        dets = []
        for det in detections:
            x1, y1, x2, y2 = map(int, det.bbox)
            conf = float(det.confidence)
            dets.append([x1, y1, x2, y2, conf])

        # Prepare simple embeddings (HSV hist) if frame is available
        embeddings = None
        if frame is not None:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                embeds = []
                for x1, y1, x2, y2, _ in dets:
                    # clamp
                    x1i = max(0, int(x1))
                    y1i = max(0, int(y1))
                    x2i = min(frame_rgb.shape[1], int(x2))
                    y2i = min(frame_rgb.shape[0], int(y2))
                    if x2i <= x1i or y2i <= y1i:
                        vec = [0.0] * 32
                    else:
                        crop = frame_rgb[y1i:y2i, x1i:x2i]
                        try:
                            hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
                            h_hist = cv2.calcHist(
                                [hsv[:, :, 0]], [0], None, [16], [0, 180]
                            ).flatten()
                            s_hist = cv2.calcHist(
                                [hsv[:, :, 1]], [0], None, [8], [0, 256]
                            ).flatten()
                            v_hist = cv2.calcHist(
                                [hsv[:, :, 2]], [0], None, [8], [0, 256]
                            ).flatten()
                            # normalize
                            h_hist = h_hist / (h_hist.sum() + 1e-6)
                            s_hist = s_hist / (s_hist.sum() + 1e-6)
                            v_hist = v_hist / (v_hist.sum() + 1e-6)
                            vec = np.concatenate([h_hist, s_hist, v_hist]).astype(float)
                            norm = np.linalg.norm(vec) + 1e-6
                            vec = (vec / norm).tolist()
                        except Exception:
                            vec = [0.0] * 32
                    embeds.append(vec)
                embeddings = embeds
            except Exception:
                embeddings = None

        online_tracks = None
        tried = []

        # Try multiple call signatures / kwarg names
        call_attempts = [
            ("update_tracks", {"frame": frame}),
            ("update_tracks", {"embeddings": embeddings}),
            ("update_tracks", {"embeds": embeddings}),
            ("update", {"frame": frame}),
            ("update", {"embeddings": embeddings}),
            ("update", {"embeds": embeddings}),
            ("update_tracks", {}),
            ("update", {}),
        ]

        for method_name, kwargs in call_attempts:
            if not hasattr(self.deep_sort, method_name):
                continue
            # remove None kwargs
            safe_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            try:
                method = getattr(self.deep_sort, method_name)
                try:
                    online_tracks = method(dets, **safe_kwargs)
                except TypeError:
                    # try without kwargs
                    online_tracks = method(dets)
                tried.append((method_name, safe_kwargs, None))
                if online_tracks is not None:
                    if self.byte_tracker is None and self.deep_sort is not None:
                        print(
                            f"[TRACKER] DeepSort used method {method_name} with kwargs {list(safe_kwargs.keys())}"
                        )
                    break
            except Exception as e:
                tried.append((method_name, safe_kwargs, str(e)))
                continue

        if online_tracks is None:
            print(
                "[TRACKER] DeepSort could not be used with any call signature, falling back to simple tracker"
            )
            if self.debug:
                print("[TRACKER] DeepSort attempts:", tried)
            return self._update_simple(detections)

        # Parse returned tracks into our Track dataclass
        tracks: list[Track] = []
        for tr in online_tracks:
            track_id = None
            bbox = None

            # track id
            if hasattr(tr, "track_id"):
                try:
                    track_id = int(tr.track_id)
                except Exception:
                    track_id = None
            elif hasattr(tr, "trackId"):
                try:
                    track_id = int(tr.trackId)
                except Exception:
                    track_id = None
            elif (
                isinstance(tr, (list, tuple))
                and len(tr) > 0
                and isinstance(tr[0], (int, str))
            ):
                try:
                    track_id = int(tr[0])
                except Exception:
                    track_id = None

            # bbox: try common attributes/methods
            if hasattr(tr, "to_tlbr"):
                try:
                    x1, y1, x2, y2 = tr.to_tlbr()
                    bbox = (float(x1), float(y1), float(x2), float(y2))
                except Exception:
                    bbox = None
            if bbox is None and hasattr(tr, "tlbr"):
                try:
                    coords = tr.tlbr
                    if isinstance(coords, (list, tuple)) and len(coords) >= 4:
                        x1, y1, x2, y2 = coords[:4]
                        bbox = (float(x1), float(y1), float(x2), float(y2))
                except Exception:
                    bbox = None

            # Some implementations return lists/tuples where one element is the bbox
            if bbox is None and isinstance(tr, (list, tuple)):
                for el in tr:
                    if (
                        isinstance(el, (list, tuple))
                        and len(el) >= 4
                        and all(isinstance(v, (int, float)) for v in el[:4])
                    ):
                        x1, y1, x2, y2 = el[:4]
                        bbox = (float(x1), float(y1), float(x2), float(y2))
                        break

            if bbox is None:
                # Can't parse bbox, skip
                continue

            team_id = self._match_team_id(bbox, detections)
            tracks.append(
                Track(
                    track_id=(track_id if track_id is not None else -1),
                    bbox=bbox,
                    confidence=1.0,
                    team_id=team_id,
                )
            )

        return tracks

    def _update_simple(self, detections: list[Detection]) -> list[Track]:
        """Fallback tracker using IoU-based greedy assignment.

        This improves over the simple center-distance matcher by using IoU to
        associate detections to existing tracks, which reduces ID fragmentation
        when objects are close together.
        """
        # If there are no existing tracks, initialize one per detection
        if not self.simple_tracks:
            for det in detections:
                self.simple_tracks.append(
                    _SimpleTrackState(
                        track_id=self.next_track_id,
                        bbox=det.bbox,
                        confidence=det.confidence,
                        team_id=det.team_id,
                        missed_frames=0,
                    )
                )
                self.next_track_id += 1

            return [
                Track(
                    track_id=t.track_id,
                    bbox=t.bbox,
                    confidence=t.confidence,
                    team_id=t.team_id,
                )
                for t in self.simple_tracks
            ]

        # Build IoU matrix between existing tracks and detections
        n_tracks = len(self.simple_tracks)
        n_dets = len(detections)

        if n_dets == 0:
            # No detections: increment missed frames and prune
            for t in self.simple_tracks:
                t.missed_frames += 1
            self.simple_tracks = [
                t
                for t in self.simple_tracks
                if t.missed_frames <= self.max_missed_frames
            ]
            return [
                Track(
                    track_id=t.track_id,
                    bbox=t.bbox,
                    confidence=t.confidence,
                    team_id=t.team_id,
                )
                for t in self.simple_tracks
            ]

        iou_mat = np.zeros((n_tracks, n_dets), dtype=float)
        for i, t in enumerate(self.simple_tracks):
            for j, d in enumerate(detections):
                iou_mat[i, j] = _bbox_iou(t.bbox, d.bbox)

        assigned_tracks = set()
        assigned_dets = set()

        # Greedy assignment: pick highest IoU pair iteratively
        IOU_THRESHOLD = 0.3
        while True:
            i, j = np.unravel_index(np.argmax(iou_mat), iou_mat.shape)
            max_iou = iou_mat[i, j]
            if max_iou < IOU_THRESHOLD:
                break
            if i in assigned_tracks or j in assigned_dets:
                iou_mat[i, j] = -1.0
                continue

            # Assign detection j to track i
            track = self.simple_tracks[i]
            det = detections[j]
            track.bbox = det.bbox
            track.confidence = det.confidence
            track.team_id = det.team_id or track.team_id
            track.missed_frames = 0

            assigned_tracks.add(i)
            assigned_dets.add(j)

            # Invalidate the assigned row/col
            iou_mat[i, :] = -1.0
            iou_mat[:, j] = -1.0

        # Remaining detections -> create new tracks
        for j, det in enumerate(detections):
            if j in assigned_dets:
                continue
            self.simple_tracks.append(
                _SimpleTrackState(
                    track_id=self.next_track_id,
                    bbox=det.bbox,
                    confidence=det.confidence,
                    team_id=det.team_id,
                    missed_frames=0,
                )
            )
            self.next_track_id += 1

        # Increment missed_frames for unassigned tracks
        for i, t in enumerate(self.simple_tracks):
            # If this track was not matched in this frame, increment missed
            # Note: we detect matched tracks by their bbox equality heuristic
            # (tracks updated above were set to detection bbox and missed_frames=0)
            if t.missed_frames == 0:
                # matched this frame
                continue
            # if t.missed_frames already > 0, it means it was not updated this frame
            # increment it now
            if i not in assigned_tracks:
                t.missed_frames += 1

        # Prune dead tracks
        self.simple_tracks = [
            t for t in self.simple_tracks if t.missed_frames <= self.max_missed_frames
        ]

        # Return Track dataclasses
        return [
            Track(
                track_id=t.track_id,
                bbox=t.bbox,
                confidence=t.confidence,
                team_id=t.team_id,
            )
            for t in self.simple_tracks
        ]

    def _find_best_match(
        self, detection: Detection, assigned_track_ids: set[int]
    ) -> _SimpleTrackState | None:
        best_track = None
        best_distance = self.distance_threshold
        det_center = self._center(detection.bbox)

        for track in self.simple_tracks:
            if track.track_id in assigned_track_ids:
                continue
            distance = math.dist(det_center, self._center(track.bbox))
            if distance < best_distance:
                best_distance = distance
                best_track = track

        return best_track

    @staticmethod
    def _center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    @staticmethod
    def _match_team_id(
        bbox: tuple[float, float, float, float], detections: list[Detection]
    ) -> str | None:
        best_iou = 0.0
        best_team = None

        for det in detections:
            iou = _bbox_iou(bbox, det.bbox)
            if iou > best_iou:
                best_iou = iou
                best_team = det.team_id

        return best_team


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
    return inter_area / union if union else 0.0

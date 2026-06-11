"""
Advanced Multi-Object Tracker with Kalman Filter, Velocity Matching, and IoU-based Association.

This module provides a robust tracking system that improves upon simple centroid-based tracking
by incorporating:
- Kalman filter for smoother predictions and handling of missing frames
- Velocity-based matching to prevent ID swaps
- IoU-based matching for bounding box overlap
- Hungarian algorithm for optimal track-detection assignment
- Occlusion handling with configurable parameters
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .types import Detection, Track

# Try to import scipy for Hungarian algorithm
try:
    from scipy.optimize import linear_sum_assignment  # type: ignore

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    linear_sum_assignment = None  # type: ignore


@dataclass(slots=True)
class KalmanState:
    """State representation for Kalman filter tracking."""

    # Position: (center_x, center_y, width, height)
    x: float  # center x
    y: float  # center y
    w: float  # width
    h: float  # height

    # Velocity: (vx, vy, vw, vh)
    vx: float = 0.0
    vy: float = 0.0
    vw: float = 0.0
    vh: float = 0.0

    # Uncertainty covariance (simplified as variance for each dimension)
    cov: np.ndarray = field(default_factory=lambda: np.eye(8) * 10.0)


@dataclass(slots=True)
class AdvancedTrackState:
    """State representation for an advanced track."""

    track_id: int
    kalman_state: KalmanState
    confidence: float
    team_id: str | None
    bbox: tuple[float, float, float, float]

    # Track history and statistics
    age: int = 0  # Number of frames this track has been active
    hits: int = 0  # Number of consecutive frames matched with detection
    missed_frames: int = 0  # Number of consecutive frames without match
    detections_count: int = 0  # Total detections associated with this track

    # Additional metadata
    metadata: dict = field(default_factory=dict)


class KalmanFilter:
    """1D Kalman Filter for tracking object motion.

    Uses a simple constant velocity model with process and measurement noise.
    State vector: [x, y, w, h, vx, vy, vw, vh]
    """

    def __init__(
        self,
        dt: float = 1.0,
        process_variance: float = 0.1,
        measurement_variance: float = 1.0,
    ):
        """Initialize Kalman Filter.

        Args:
            dt: Time delta between frames (default 1.0)
            process_variance: Process noise covariance (higher = less trust in model)
            measurement_variance: Measurement noise covariance (higher = less trust in measurements)
        """
        self.dt = dt
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance

        # State transition matrix (constant velocity model)
        self.F = np.array(
            [
                [1, 0, 0, 0, dt, 0, 0, 0],  # x = x + vx*dt
                [0, 1, 0, 0, 0, dt, 0, 0],  # y = y + vy*dt
                [0, 0, 1, 0, 0, 0, dt, 0],  # w = w + vw*dt
                [0, 0, 0, 1, 0, 0, 0, dt],  # h = h + vh*dt
                [0, 0, 0, 0, 1, 0, 0, 0],  # vx = vx (constant)
                [0, 0, 0, 0, 0, 1, 0, 0],  # vy = vy (constant)
                [0, 0, 0, 0, 0, 0, 1, 0],  # vw = vw (constant)
                [0, 0, 0, 0, 0, 0, 0, 1],  # vh = vh (constant)
            ],
            dtype=float,
        )

        # Measurement matrix (we only measure position and size, not velocity)
        self.H = np.array(
            [
                [1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 0],
            ],
            dtype=float,
        )

        # Process noise covariance
        self.Q = np.eye(8) * process_variance

        # Measurement noise covariance
        self.R = np.eye(4) * measurement_variance

    def predict(self, state: KalmanState) -> KalmanState:
        """Predict next state using the constant velocity model.

        Args:
            state: Current state

        Returns:
            Predicted state
        """
        # Convert state to vector
        x_vec = np.array(
            [
                state.x,
                state.y,
                state.w,
                state.h,
                state.vx,
                state.vy,
                state.vw,
                state.vh,
            ],
            dtype=float,
        )

        # Predict state
        x_pred = self.F @ x_vec

        # Update covariance
        cov_pred = self.F @ state.cov @ self.F.T + self.Q

        # Create new state
        new_state = KalmanState(
            x=x_pred[0],
            y=x_pred[1],
            w=x_pred[2],
            h=x_pred[3],
            vx=x_pred[4],
            vy=x_pred[5],
            vw=x_pred[6],
            vh=x_pred[7],
            cov=cov_pred,
        )

        return new_state

    def update(
        self, state: KalmanState, measurement: tuple[float, float, float, float]
    ) -> KalmanState:
        """Update state with measurement (bbox).

        Args:
            state: Predicted state
            measurement: Measured bbox (x, y, w, h)

        Returns:
            Updated state
        """
        # Convert measurement to vector
        z = np.array(
            [measurement[0], measurement[1], measurement[2], measurement[3]],
            dtype=float,
        )

        # Convert state to vector
        x_vec = np.array(
            [
                state.x,
                state.y,
                state.w,
                state.h,
                state.vx,
                state.vy,
                state.vw,
                state.vh,
            ],
            dtype=float,
        )

        # Innovation
        y = z - self.H @ x_vec

        # Innovation covariance
        S = self.H @ state.cov @ self.H.T + self.R

        # Kalman gain
        K = state.cov @ self.H.T @ np.linalg.inv(S)

        # Update state
        x_updated = x_vec + K @ y

        # Update covariance
        identity_matrix = np.eye(8)
        cov_updated = (identity_matrix - K @ self.H) @ state.cov

        # Create new state
        new_state = KalmanState(
            x=x_updated[0],
            y=x_updated[1],
            w=x_updated[2],
            h=x_updated[3],
            vx=x_updated[4],
            vy=x_updated[5],
            vw=x_updated[6],
            vh=x_updated[7],
            cov=cov_updated,
        )

        return new_state


class AdvancedMultiObjectTracker:
    """Advanced multi-object tracker with Kalman filter and multiple matching strategies.

    Features:
    - Kalman filter for motion prediction
    - Distance-based matching (centroid)
    - Velocity-based matching (direction and speed)
    - IoU-based matching (bounding box overlap)
    - Hungarian algorithm for optimal assignment (if scipy available)
    - Configurable occlusion handling
    """

    def __init__(
        self,
        fps: int = 25,
        max_missed_frames: int = 30,
        max_age: int = 100,
        distance_threshold: float = 100.0,
        iou_threshold: float = 0.3,
        velocity_weight: float = 0.3,
        use_kalman: bool = True,
        use_hungarian: bool = True,
        kalman_process_var: float = 0.1,
        kalman_measurement_var: float = 1.0,
    ):
        """Initialize the advanced tracker.

        Args:
            fps: Frames per second (used for time delta in Kalman)
            max_missed_frames: Maximum consecutive frames without detection before track removal
            max_age: Maximum age of a track in frames
            distance_threshold: Maximum centroid distance for matching (pixels)
            iou_threshold: Minimum IoU for matching
            velocity_weight: Weight for velocity component in matching score (0.0-1.0)
            use_kalman: Whether to use Kalman filter for prediction
            use_hungarian: Whether to use Hungarian algorithm for optimal assignment
            kalman_process_var: Kalman process noise variance
            kalman_measurement_var: Kalman measurement noise variance
        """
        self.fps = fps
        self.dt = 1.0 / fps
        self.max_missed_frames = max_missed_frames
        self.max_age = max_age
        self.distance_threshold = distance_threshold
        self.iou_threshold = iou_threshold
        self.velocity_weight = max(0.0, min(1.0, velocity_weight))
        self.use_kalman = use_kalman
        self.use_hungarian = use_hungarian and HAS_SCIPY

        self.next_track_id = 1
        self.tracks: list[AdvancedTrackState] = []

        # Initialize Kalman filter
        if self.use_kalman:
            self.kalman = KalmanFilter(
                dt=self.dt,
                process_variance=kalman_process_var,
                measurement_variance=kalman_measurement_var,
            )
        else:
            self.kalman = None

    def update(
        self, frame_shape: tuple[int, int, int], detections: list[Detection]
    ) -> list[Track]:
        """Update tracker with new detections.

        Args:
            frame_shape: Shape of the current frame (height, width, channels)
            detections: List of Detection objects from the detector

        Returns:
            List of Track objects with updated positions
        """
        # Predict next state for all tracks
        for track in self.tracks:
            if self.use_kalman and self.kalman is not None:
                track.kalman_state = self.kalman.predict(track.kalman_state)
                track.bbox = self._state_to_bbox(track.kalman_state)
            track.missed_frames += 1

        # Find associations between tracks and detections
        if detections:
            if self.use_hungarian:
                associations = self._associate_hungarian(self.tracks, detections)
            else:
                associations = self._associate_greedy(self.tracks, detections)
        else:
            associations = []

        # Update tracks with detections
        matched_track_ids = set()
        for track_idx, det_idx in associations:
            track = self.tracks[track_idx]
            detection = detections[det_idx]

            # Update Kalman state with measurement
            if self.use_kalman and self.kalman is not None:
                track.kalman_state = self.kalman.update(
                    track.kalman_state, self._bbox_to_state(detection.bbox)
                )

            track.bbox = detection.bbox
            track.confidence = detection.confidence
            track.team_id = detection.team_id or track.team_id
            track.missed_frames = 0
            track.hits += 1
            track.detections_count += 1
            matched_track_ids.add(track.track_id)

        # Create new tracks for unmatched detections
        matched_det_ids = set(det_idx for _, det_idx in associations)
        for det_idx, detection in enumerate(detections):
            if det_idx not in matched_det_ids:
                self._create_track(detection)

        # Remove dead tracks
        self.tracks = [
            t
            for t in self.tracks
            if t.missed_frames <= self.max_missed_frames and t.age <= self.max_age
        ]

        # Increment age for all tracks
        for track in self.tracks:
            track.age += 1

        # Convert to Track objects and return
        return [
            Track(
                track_id=track.track_id,
                bbox=track.bbox,
                confidence=track.confidence,
                team_id=track.team_id,
                metadata={
                    "age": track.age,
                    "hits": track.hits,
                    "missed_frames": track.missed_frames,
                    "detections_count": track.detections_count,
                },
            )
            for track in self.tracks
        ]

    def _associate_hungarian(
        self, tracks: list[AdvancedTrackState], detections: list[Detection]
    ) -> list[tuple[int, int]]:
        """Associate tracks to detections using Hungarian algorithm.

        Args:
            tracks: List of tracks
            detections: List of detections

        Returns:
            List of (track_idx, det_idx) tuples representing associations
        """
        if not tracks or not detections:
            return []

        # Build cost matrix
        cost_matrix = np.zeros((len(tracks), len(detections)))

        for i, track in enumerate(tracks):
            for j, detection in enumerate(detections):
                cost = self._compute_association_cost(track, detection)
                cost_matrix[i, j] = cost

        # Apply Hungarian algorithm
        if linear_sum_assignment is not None:
            track_indices, det_indices = linear_sum_assignment(cost_matrix)

            # Filter by maximum cost threshold
            associations = []
            for track_idx, det_idx in zip(track_indices, det_indices):
                if cost_matrix[track_idx, det_idx] < 1.0:  # Normalize to 0-1 scale
                    associations.append((track_idx, det_idx))

            return associations

        return []

    def _associate_greedy(
        self, tracks: list[AdvancedTrackState], detections: list[Detection]
    ) -> list[tuple[int, int]]:
        """Associate tracks to detections using greedy algorithm.

        Args:
            tracks: List of tracks
            detections: List of detections

        Returns:
            List of (track_idx, det_idx) tuples representing associations
        """
        associations = []
        used_detection_indices = set()

        # Create list of (track_idx, det_idx, cost) tuples
        candidates = []
        for i, track in enumerate(tracks):
            for j, detection in enumerate(detections):
                cost = self._compute_association_cost(track, detection)
                if cost < 1.0:  # Only consider candidates below threshold
                    candidates.append((i, j, cost))

        # Sort by cost (best first)
        candidates.sort(key=lambda x: x[2])

        # Greedily assign
        for track_idx, det_idx, _ in candidates:
            if det_idx not in used_detection_indices and not any(
                t_idx == track_idx for t_idx, _ in associations
            ):
                associations.append((track_idx, det_idx))
                used_detection_indices.add(det_idx)

        return associations

    def _compute_association_cost(
        self, track: AdvancedTrackState, detection: Detection
    ) -> float:
        """Compute association cost between track and detection.

        Combines:
        - Distance-based cost (centroid distance)
        - Velocity-based cost (expected motion)
        - IoU-based cost (bounding box overlap)

        Args:
            track: Track state
            detection: Detection

        Returns:
            Cost value (lower is better, normalized to 0-1)
        """
        # Distance-based cost (0-1)
        dist_cost = self._distance_cost(track, detection)

        # Velocity-based cost (0-1)
        vel_cost = self._velocity_cost(track, detection)

        # IoU-based cost (0-1, where 1 - IoU)
        iou_cost = self._iou_cost(track, detection)

        # Combine costs with weights
        # (1 - velocity_weight) = distance_weight
        distance_weight = 1.0 - self.velocity_weight

        combined_cost = (
            distance_weight * dist_cost
            + self.velocity_weight * vel_cost
            + 0.5 * iou_cost  # IoU as secondary cost
        )

        return min(1.0, combined_cost)

    def _distance_cost(self, track: AdvancedTrackState, detection: Detection) -> float:
        """Compute distance-based cost using centroid distance.

        Args:
            track: Track state
            detection: Detection

        Returns:
            Cost value (0-1, where 0 = exact match)
        """
        track_center = self._get_center(track.bbox)
        det_center = self._get_center(detection.bbox)

        distance = math.dist(track_center, det_center)

        # Normalize to 0-1 scale using distance_threshold
        # If distance > threshold, return 1.0
        normalized = distance / self.distance_threshold
        return min(1.0, normalized)

    def _velocity_cost(self, track: AdvancedTrackState, detection: Detection) -> float:
        """Compute velocity-based cost.

        Compares expected position (based on velocity) with detection position.

        Args:
            track: Track state
            detection: Detection

        Returns:
            Cost value (0-1)
        """
        if not self.use_kalman or track.hits < 2:
            return 0.5  # Neutral cost if not enough history

        # Get expected position from Kalman state
        expected_center = (track.kalman_state.x, track.kalman_state.y)
        det_center = self._get_center(detection.bbox)

        # Distance from expected position
        expected_distance = math.dist(expected_center, det_center)

        # Normalize to 0-1
        normalized = expected_distance / self.distance_threshold
        return min(1.0, normalized)

    def _iou_cost(self, track: AdvancedTrackState, detection: Detection) -> float:
        """Compute IoU-based cost.

        Args:
            track: Track state
            detection: Detection

        Returns:
            Cost value (0-1, where 0 = maximum IoU, 1 = no overlap)
        """
        iou = self._bbox_iou(track.bbox, detection.bbox)

        # Cost = 1 - IoU (so higher IoU = lower cost)
        cost = 1.0 - iou

        # Apply threshold: if IoU < threshold, return maximum cost
        if iou < self.iou_threshold:
            return 1.0

        return cost

    def _create_track(self, detection: Detection) -> None:
        """Create a new track from a detection.

        Args:
            detection: Detection object
        """
        cx = (detection.bbox[0] + detection.bbox[2]) / 2.0
        cy = (detection.bbox[1] + detection.bbox[3]) / 2.0
        w = detection.bbox[2] - detection.bbox[0]
        h = detection.bbox[3] - detection.bbox[1]
        kalman_state = KalmanState(
            x=cx, y=cy, w=w, h=h,
        )

        track = AdvancedTrackState(
            track_id=self.next_track_id,
            kalman_state=kalman_state,
            confidence=detection.confidence,
            team_id=detection.team_id,
            bbox=detection.bbox,
            age=0,
            hits=1,
            missed_frames=0,
            detections_count=1,
        )

        self.tracks.append(track)
        self.next_track_id += 1

    @staticmethod
    def _get_center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
        """Get center point of bounding box.

        Args:
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            Center point (cx, cy)
        """
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    @staticmethod
    def _bbox_to_state(
        bbox: tuple[float, float, float, float],
    ) -> tuple[float, float, float, float]:
        """Convert bbox from (x1, y1, x2, y2) to (cx, cy, w, h).

        Args:
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            State format (cx, cy, w, h)
        """
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        w = x2 - x1
        h = y2 - y1
        return (cx, cy, w, h)

    @staticmethod
    def _state_to_bbox(state: KalmanState) -> tuple[float, float, float, float]:
        """Convert state (cx, cy, w, h) to bbox (x1, y1, x2, y2).

        Args:
            state: Kalman state

        Returns:
            Bounding box (x1, y1, x2, y2)
        """
        x1 = state.x - state.w / 2.0
        y1 = state.y - state.h / 2.0
        x2 = state.x + state.w / 2.0
        y2 = state.y + state.h / 2.0
        return (x1, y1, x2, y2)

    @staticmethod
    def _bbox_iou(
        a: tuple[float, float, float, float], b: tuple[float, float, float, float]
    ) -> float:
        """Compute Intersection over Union (IoU) for two bounding boxes.

        Args:
            a: First bounding box (x1, y1, x2, y2)
            b: Second bounding box (x1, y1, x2, y2)

        Returns:
            IoU value (0.0-1.0)
        """
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b

        # Intersection
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        # Union
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - inter_area

        return inter_area / union if union > 0.0 else 0.0

"""
Thread-safe circular frame buffer for video processing.

Features:
- Circular/ring buffer implementation
- Thread-safe with Queue
- Performance metrics (frame rate, buffer usage)
- Configurable buffer size
- Optional compression
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BufferMetrics:
    """Buffer performance metrics."""

    frames_added: int = 0
    frames_removed: int = 0
    frames_dropped: int = 0
    total_time_ms: float = 0.0
    min_buffer_size: int = 0
    max_buffer_size: int = 0
    current_buffer_size: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def fps(self) -> float:
        """Calculate frames per second."""
        elapsed_seconds = time.time() - self.start_time
        if elapsed_seconds <= 0:
            return 0.0
        return self.frames_added / elapsed_seconds

    @property
    def buffer_usage_percent(self) -> float:
        """Calculate buffer usage percentage."""
        if self.max_buffer_size <= 0:
            return 0.0
        return (self.current_buffer_size / self.max_buffer_size) * 100

    @property
    def drop_rate_percent(self) -> float:
        """Calculate drop rate percentage."""
        total = self.frames_added + self.frames_dropped
        if total <= 0:
            return 0.0
        return (self.frames_dropped / total) * 100

    def __str__(self) -> str:
        return (
            f"Frames: {self.frames_added} added, {self.frames_removed} removed, "
            f"{self.frames_dropped} dropped | "
            f"FPS: {self.fps:.1f} | "
            f"Buffer: {self.current_buffer_size}/{self.max_buffer_size} "
            f"({self.buffer_usage_percent:.1f}%) | "
            f"Drop rate: {self.drop_rate_percent:.2f}%"
        )


class FrameBuffer:
    """Thread-safe circular frame buffer."""

    def __init__(
        self,
        max_size: int = 30,
        enable_compression: bool = False,
        compression_quality: int = 95,
    ) -> None:
        """
        Initialize frame buffer.

        Args:
            max_size: Maximum number of frames to buffer
            enable_compression: Enable frame compression (JPEG)
            compression_quality: JPEG compression quality (1-100)
        """
        if max_size < 1:
            raise ValueError("Buffer size must be at least 1")

        self.max_size = max_size
        self.enable_compression = enable_compression
        self.compression_quality = compression_quality

        # Use deque for efficient O(1) append and popleft
        self._buffer: deque[np.ndarray] = deque(maxlen=max_size)
        self._timestamps: deque[float] = deque(maxlen=max_size)
        self._frame_indices: deque[int] = deque(maxlen=max_size)

        # Thread safety
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

        # Metrics
        self.metrics = BufferMetrics(max_buffer_size=max_size)

        # Event callbacks
        self._on_frame_added: Optional[Callable] = None
        self._on_buffer_full: Optional[Callable] = None

    def put(
        self,
        frame: np.ndarray,
        frame_index: int = 0,
        timestamp: Optional[float] = None,
        block: bool = False,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Add frame to buffer.

        Args:
            frame: Frame data as numpy array
            frame_index: Frame index/number
            timestamp: Frame timestamp (default: current time)
            block: Block if buffer full
            timeout: Timeout in seconds (only if block=True)

        Returns:
            True if frame added, False if dropped/failed
        """
        if timestamp is None:
            timestamp = time.time()

        try:
            with self._not_full:
                # Check if buffer is full
                if len(self._buffer) >= self.max_size:
                    if block:
                        # Wait for space
                        acquired = self._not_full.wait(timeout=timeout)
                        if not acquired:
                            logger.warning("Buffer put timeout")
                            self.metrics.frames_dropped += 1
                            return False
                    else:
                        # Drop frame
                        logger.debug("Buffer full, dropping frame")
                        self.metrics.frames_dropped += 1

                        # Notify if callback set
                        if self._on_buffer_full:
                            self._on_buffer_full()

                        return False

                # Apply compression if enabled
                frame_to_store = frame
                if self.enable_compression:
                    frame_to_store = self._compress_frame(frame)

                # Add to buffer
                self._buffer.append(frame_to_store)
                self._timestamps.append(timestamp)
                self._frame_indices.append(frame_index)

                # Update metrics
                self.metrics.frames_added += 1
                self.metrics.current_buffer_size = len(self._buffer)
                self.metrics.min_buffer_size = min(
                    self.metrics.min_buffer_size,
                    len(self._buffer),
                )

                # Notify waiting threads
                self._not_empty.notify_all()

                # Callback
                if self._on_frame_added:
                    self._on_frame_added()

                return True

        except Exception as e:
            logger.error(f"Error adding frame to buffer: {e}")
            self.metrics.frames_dropped += 1
            return False

    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Optional[tuple[np.ndarray, int, float]]:
        """
        Retrieve frame from buffer.

        Args:
            block: Block if buffer empty
            timeout: Timeout in seconds (only if block=True)

        Returns:
            Tuple of (frame, frame_index, timestamp) or None if empty/timeout
        """
        try:
            with self._not_empty:
                # Check if buffer has frames
                if len(self._buffer) == 0:
                    if block:
                        # Wait for data
                        acquired = self._not_empty.wait(timeout=timeout)
                        if not acquired:
                            logger.debug("Buffer get timeout")
                            return None
                    else:
                        return None

                # Get frame (FIFO)
                frame = self._buffer.popleft()
                frame_index = self._frame_indices.popleft()
                timestamp = self._timestamps.popleft()

                # Decompress if needed
                if self.enable_compression:
                    frame = self._decompress_frame(frame)

                # Update metrics
                self.metrics.frames_removed += 1
                self.metrics.current_buffer_size = len(self._buffer)

                # Notify waiting threads
                self._not_full.notify_all()

                return frame, frame_index, timestamp

        except Exception as e:
            logger.error(f"Error getting frame from buffer: {e}")
            return None

    def peek(self, index: int = 0) -> Optional[np.ndarray]:
        """
        View frame without removing (peek).

        Args:
            index: Frame index in buffer (0 = oldest)

        Returns:
            Frame data or None
        """
        try:
            with self._lock:
                if index < 0 or index >= len(self._buffer):
                    return None

                frame = self._buffer[index]

                if self.enable_compression:
                    frame = self._decompress_frame(frame)

                return frame

        except Exception as e:
            logger.error(f"Error peeking at frame: {e}")
            return None

    def size(self) -> int:
        """Get current number of frames in buffer."""
        with self._lock:
            return len(self._buffer)

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        with self._lock:
            return len(self._buffer) == 0

    def is_full(self) -> bool:
        """Check if buffer is full."""
        with self._lock:
            return len(self._buffer) >= self.max_size

    def clear(self) -> None:
        """Clear all frames from buffer."""
        with self._lock:
            self._buffer.clear()
            self._timestamps.clear()
            self._frame_indices.clear()
            self.metrics.current_buffer_size = 0
            self._not_empty.notify_all()
            self._not_full.notify_all()

    def get_all(self) -> list[tuple[np.ndarray, int, float]]:
        """Get all frames and clear buffer."""
        frames = []
        while not self.is_empty():
            result = self.get(block=False)
            if result:
                frames.append(result)
        return frames

    def set_callback_frame_added(self, callback: Callable) -> None:
        """Set callback for when frame is added."""
        self._on_frame_added = callback

    def set_callback_buffer_full(self, callback: Callable) -> None:
        """Set callback for when buffer becomes full."""
        self._on_buffer_full = callback

    def get_metrics(self) -> BufferMetrics:
        """Get buffer metrics."""
        with self._lock:
            return self.metrics

    def reset_metrics(self) -> None:
        """Reset metrics."""
        with self._lock:
            self.metrics = BufferMetrics(max_buffer_size=self.max_size)

    def log_metrics(self) -> None:
        """Log buffer metrics."""
        with self._lock:
            logger.info(f"Buffer Metrics: {self.metrics}")

    def _compress_frame(self, frame: np.ndarray) -> bytes:
        """Compress frame using JPEG."""
        try:
            import cv2

            ret, buffer = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, self.compression_quality],
            )
            if ret:
                return buffer.tobytes()
        except Exception as e:
            logger.warning(f"Frame compression failed: {e}")
        return frame

    def _decompress_frame(self, data: bytes | np.ndarray) -> np.ndarray:
        """Decompress frame from JPEG."""
        try:
            import cv2

            if isinstance(data, bytes):
                frame_array = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                if frame is not None:
                    return frame
        except Exception as e:
            logger.warning(f"Frame decompression failed: {e}")
        return data


class FrameBufferPool:
    """Manages multiple frame buffers."""

    def __init__(self, num_buffers: int = 1, buffer_size: int = 30) -> None:
        """
        Initialize buffer pool.

        Args:
            num_buffers: Number of buffers to create
            buffer_size: Size of each buffer
        """
        self.buffers: dict[str, FrameBuffer] = {}

        for i in range(num_buffers):
            name = f"buffer_{i}"
            self.buffers[name] = FrameBuffer(max_size=buffer_size)

    def get_buffer(self, name: str = "buffer_0") -> Optional[FrameBuffer]:
        """Get buffer by name."""
        return self.buffers.get(name)

    def add_buffer(self, name: str, buffer_size: int = 30) -> FrameBuffer:
        """Add new buffer to pool."""
        buffer = FrameBuffer(max_size=buffer_size)
        self.buffers[name] = buffer
        return buffer

    def get_all_buffers(self) -> dict[str, FrameBuffer]:
        """Get all buffers."""
        return self.buffers.copy()

    def get_metrics(self) -> dict[str, BufferMetrics]:
        """Get metrics for all buffers."""
        return {name: buf.get_metrics() for name, buf in self.buffers.items()}

    def log_all_metrics(self) -> None:
        """Log metrics for all buffers."""
        for name, buf in self.buffers.items():
            logger.info(f"[{name}] {buf.get_metrics()}")


class AdaptiveBuffer:
    """
    Adaptive buffer that adjusts size based on performance metrics.

    Features:
    - Automatic buffer size adjustment
    - Drop detection and recovery
    - Performance optimization
    """

    def __init__(
        self,
        initial_size: int = 30,
        min_size: int = 5,
        max_size: int = 100,
        adjust_interval_seconds: float = 5.0,
    ) -> None:
        """
        Initialize adaptive buffer.

        Args:
            initial_size: Initial buffer size
            min_size: Minimum buffer size
            max_size: Maximum buffer size
            adjust_interval_seconds: Interval between adjustments
        """
        self.min_size = min_size
        self.max_size = max_size
        self.adjust_interval_seconds = adjust_interval_seconds

        self._buffer = FrameBuffer(max_size=initial_size)
        self._last_adjust_time = time.time()
        self._last_drop_rate = 0.0
        self._lock = threading.Lock()

    def put(self, frame: np.ndarray, frame_index: int = 0) -> bool:
        """Add frame to buffer."""
        result = self._buffer.put(frame, frame_index=frame_index, block=False)
        self._try_adjust_size()
        return result

    def get(self, block: bool = True, timeout: Optional[float] = None):
        """Get frame from buffer."""
        return self._buffer.get(block=block, timeout=timeout)

    def _try_adjust_size(self) -> None:
        """Try to adjust buffer size based on metrics."""
        with self._lock:
            now = time.time()
            if (now - self._last_adjust_time) < self.adjust_interval_seconds:
                return

            metrics = self._buffer.get_metrics()
            current_drop_rate = metrics.drop_rate_percent

            # Check if we need to increase buffer
            if current_drop_rate > 5.0:  # More than 5% drops
                new_size = min(
                    self._buffer.max_size + 10,
                    self.max_size,
                )
                if new_size > self._buffer.max_size:
                    logger.info(
                        f"Increasing buffer size from {self._buffer.max_size} to {new_size} "
                        f"(drop rate: {current_drop_rate:.2f}%)"
                    )
                    self._buffer.max_size = new_size

            # Check if we can decrease buffer
            elif current_drop_rate == 0.0 and metrics.buffer_usage_percent < 30:
                new_size = max(
                    self._buffer.max_size - 5,
                    self.min_size,
                )
                if new_size < self._buffer.max_size:
                    logger.info(
                        f"Decreasing buffer size from {self._buffer.max_size} to {new_size}"
                    )
                    self._buffer.max_size = new_size

            self._last_adjust_time = now
            self._last_drop_rate = current_drop_rate

    def get_buffer(self) -> FrameBuffer:
        """Get underlying buffer."""
        return self._buffer

    def get_metrics(self) -> BufferMetrics:
        """Get metrics."""
        return self._buffer.get_metrics()

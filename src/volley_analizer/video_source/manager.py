"""Video source manager for handling different video sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import cv2


class VideoSourceType(Enum):
    """Enumeration of supported video source types."""

    LOCAL_FILE = "file"
    STREAMING_URL = "streaming"
    WEBCAM = "webcam"


@dataclass
class VideoMetadata:
    """Metadata for video source."""

    width: int
    height: int
    fps: float
    frame_count: Optional[int] = None
    duration_seconds: Optional[float] = None
    is_streaming: bool = False


@dataclass
class VideoSourceInfo:
    """Information about a video source."""

    source_type: VideoSourceType
    source_path: str
    name: str = ""
    metadata: Optional[VideoMetadata] = None
    is_accessible: bool = False
    error_message: str = ""
    extra_info: dict = field(default_factory=dict)

    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{self.name} ({self.source_type.value})"


class VideoSourceManager:
    """Manager for handling different video sources."""

    def __init__(self) -> None:
        """Initialize the video source manager."""
        self.current_source: Optional[VideoSourceInfo] = None
        self._cached_webcams: Optional[list[dict]] = None

    def detect_webcams(self) -> list[dict]:
        """Detect available webcams on the system.

        Returns:
            List of dictionaries containing webcam info with keys:
            - index: int (webcam index)
            - name: str (display name)
            - is_available: bool
        """
        if self._cached_webcams is not None:
            return self._cached_webcams

        webcams = []
        for idx in range(10):  # Check first 10 indices
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                # Try to get device name (platform-specific)
                name = f"Webcam {idx}"
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

                webcams.append(
                    {
                        "index": idx,
                        "name": name,
                        "is_available": True,
                        "resolution": f"{width}x{height}",
                        "fps": fps,
                    }
                )
                cap.release()
            else:
                cap.release()

        self._cached_webcams = webcams
        return webcams

    def get_local_file_info(self, file_path: str) -> VideoSourceInfo:
        """Get information about a local video file.

        Args:
            file_path: Path to the video file

        Returns:
            VideoSourceInfo object with metadata and accessibility info
        """
        path = Path(file_path)
        info = VideoSourceInfo(
            source_type=VideoSourceType.LOCAL_FILE,
            source_path=file_path,
            name=path.name,
        )

        if not path.exists():
            info.error_message = f"File not found: {file_path}"
            return info

        if not path.is_file():
            info.error_message = f"Path is not a file: {file_path}"
            return info

        try:
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                info.error_message = "Cannot open video file"
                cap.release()
                return info

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

            duration = (frame_count / fps) if fps and frame_count else 0.0

            info.metadata = VideoMetadata(
                width=width,
                height=height,
                fps=fps,
                frame_count=frame_count,
                duration_seconds=duration,
                is_streaming=False,
            )
            info.is_accessible = True
            cap.release()

        except Exception as exc:
            info.error_message = f"Error reading video: {str(exc)}"

        return info

    def get_streaming_info(self, url: str) -> VideoSourceInfo:
        """Get information about a streaming source.

        Args:
            url: Streaming URL (HTTP, RTSP, etc.)

        Returns:
            VideoSourceInfo object with connectivity info
        """
        info = VideoSourceInfo(
            source_type=VideoSourceType.STREAMING_URL,
            source_path=url,
            name=url.split("/")[-1] or "Stream",
        )

        # Basic URL validation
        if not url.startswith(("http://", "https://", "rtsp://", "rtmp://")):
            info.error_message = "Invalid stream URL format"
            return info

        # Try to open stream with timeout
        try:
            cap = cv2.VideoCapture(url)

            # For streaming, we use a timeout approach
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

                # Streaming sources don't have frame count or duration
                info.metadata = VideoMetadata(
                    width=width,
                    height=height,
                    fps=fps,
                    frame_count=None,
                    duration_seconds=None,
                    is_streaming=True,
                )
                info.is_accessible = True

                # Show connection status
                if width > 0 and height > 0:
                    info.extra_info["connection_status"] = "connected"
                else:
                    info.extra_info["connection_status"] = "unstable"

                cap.release()
            else:
                info.error_message = (
                    "Cannot connect to stream (check URL and connectivity)"
                )
                cap.release()

        except Exception as exc:
            info.error_message = f"Stream error: {str(exc)}"

        return info

    def get_webcam_info(self, webcam_index: int) -> VideoSourceInfo:
        """Get information about a webcam source.

        Args:
            webcam_index: Index of the webcam

        Returns:
            VideoSourceInfo object with webcam info
        """
        webcams = self.detect_webcams()
        webcam_data = next((w for w in webcams if w["index"] == webcam_index), None)

        if not webcam_data:
            return VideoSourceInfo(
                source_type=VideoSourceType.WEBCAM,
                source_path=str(webcam_index),
                name=f"Webcam {webcam_index}",
                error_message="Webcam not found",
            )

        try:
            cap = cv2.VideoCapture(webcam_index)
            if not cap.isOpened():
                cap.release()
                return VideoSourceInfo(
                    source_type=VideoSourceType.WEBCAM,
                    source_path=str(webcam_index),
                    name=webcam_data["name"],
                    error_message="Cannot open webcam",
                )

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

            info = VideoSourceInfo(
                source_type=VideoSourceType.WEBCAM,
                source_path=str(webcam_index),
                name=webcam_data["name"],
                metadata=VideoMetadata(
                    width=width,
                    height=height,
                    fps=fps,
                    is_streaming=True,  # Webcam is streaming
                ),
                is_accessible=True,
            )
            cap.release()
            return info

        except Exception as exc:
            return VideoSourceInfo(
                source_type=VideoSourceType.WEBCAM,
                source_path=str(webcam_index),
                name=f"Webcam {webcam_index}",
                error_message=f"Error accessing webcam: {str(exc)}",
            )

    def capture_first_frame(
        self, source_info: VideoSourceInfo, max_attempts: int = 5
    ) -> Optional[any]:
        """Capture the first frame from a video source.

        Args:
            source_info: VideoSourceInfo object
            max_attempts: Maximum attempts for streaming sources

        Returns:
            Frame as numpy array or None if capture failed
        """
        if source_info.source_type == VideoSourceType.LOCAL_FILE:
            cap = cv2.VideoCapture(source_info.source_path)
        elif source_info.source_type == VideoSourceType.WEBCAM:
            cap = cv2.VideoCapture(int(source_info.source_path))
        elif source_info.source_type == VideoSourceType.STREAMING_URL:
            cap = cv2.VideoCapture(source_info.source_path)
        else:
            return None

        frame = None
        try:
            attempts = 0
            while attempts < max_attempts:
                ret, f = cap.read()
                if ret:
                    frame = f
                    break
                attempts += 1

        finally:
            cap.release()

        return frame

    def set_current_source(self, source_info: VideoSourceInfo) -> None:
        """Set the current video source.

        Args:
            source_info: VideoSourceInfo object to set as current
        """
        if not source_info.is_accessible:
            raise ValueError(f"Source is not accessible: {source_info.error_message}")

        self.current_source = source_info

    def validate_codec_support(self, source_info: VideoSourceInfo) -> dict:
        """Validate codec support for a video source.

        Returns:
            Dictionary with codec information
        """
        result = {
            "is_supported": False,
            "codec": "unknown",
            "message": "",
        }

        if source_info.source_type == VideoSourceType.LOCAL_FILE:
            try:
                cap = cv2.VideoCapture(source_info.source_path)
                if cap.isOpened():
                    # Get codec fourcc
                    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                    codec_str = "".join(
                        [chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]
                    )
                    result["codec"] = codec_str
                    result["is_supported"] = True
                    cap.release()
            except Exception as exc:
                result["message"] = str(exc)
        else:
            # Streaming and webcam are generally supported
            result["is_supported"] = True
            result["codec"] = "stream"

        return result

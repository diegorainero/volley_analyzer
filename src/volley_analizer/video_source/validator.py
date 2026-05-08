"""Video source validation module."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .manager import VideoSourceInfo, VideoSourceType


class ValidationResult:
    """Result of a video source validation."""

    def __init__(self) -> None:
        """Initialize validation result."""
        self.is_valid = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.suggestions: list[str] = []

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_suggestion(self, message: str) -> None:
        """Add a suggestion message."""
        self.suggestions.append(message)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
        }


class VideoSourceValidator:
    """Validator for video sources."""

    # Supported video extensions
    SUPPORTED_EXTENSIONS = {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".flv",
        ".wmv",
        ".webm",
        ".m4v",
    }

    # Supported streaming protocols
    SUPPORTED_PROTOCOLS = {
        "http://",
        "https://",
        "rtsp://",
        "rtmp://",
        "hls://",
        "dash://",
    }

    @staticmethod
    def validate_local_file(source_info: VideoSourceInfo) -> ValidationResult:
        """Validate a local video file.

        Args:
            source_info: VideoSourceInfo object for a local file

        Returns:
            ValidationResult object
        """
        result = ValidationResult()

        if source_info.source_type != VideoSourceType.LOCAL_FILE:
            result.add_error("Source is not a local file")
            return result

        path = Path(source_info.source_path)

        # Check file exists
        if not path.exists():
            result.add_error(f"File does not exist: {path}")
            result.add_suggestion("Check the file path and try again")
            return result

        # Check file is a file, not a directory
        if not path.is_file():
            result.add_error(f"Path is not a file: {path}")
            return result

        # Check file extension
        if path.suffix.lower() not in VideoSourceValidator.SUPPORTED_EXTENSIONS:
            result.add_warning(
                f"Unsupported file extension: {path.suffix} "
                f"(supported: {', '.join(VideoSourceValidator.SUPPORTED_EXTENSIONS)})"
            )

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb < 1:
            result.add_warning("Video file is very small (<1 MB), might be corrupted")
        if file_size_mb > 5000:  # > 5 GB
            result.add_warning(
                f"Video file is large ({file_size_mb:.0f} MB), analysis may take time"
            )

        # Check metadata availability
        if not source_info.metadata:
            result.add_error("Cannot read video metadata")
            result.add_suggestion(
                "Try using a different video player to verify the file"
            )
            return result

        # Validate metadata values
        if source_info.metadata.width <= 0 or source_info.metadata.height <= 0:
            result.add_error("Invalid video resolution")
            return result

        if source_info.metadata.fps <= 0:
            result.add_warning("Invalid or missing FPS information")
            result.add_suggestion("Some videos may not have proper FPS metadata")

        if source_info.metadata.duration_seconds <= 0:
            result.add_warning("Invalid or missing duration information")

        # Check accessibility
        if not source_info.is_accessible:
            result.add_error(source_info.error_message or "Cannot access video file")
            result.add_suggestion("Check file permissions and file format support")

        return result

    @staticmethod
    def validate_streaming_url(source_info: VideoSourceInfo) -> ValidationResult:
        """Validate a streaming URL.

        Args:
            source_info: VideoSourceInfo object for a streaming source

        Returns:
            ValidationResult object
        """
        result = ValidationResult()

        if source_info.source_type != VideoSourceType.STREAMING_URL:
            result.add_error("Source is not a streaming URL")
            return result

        url = source_info.source_path

        # Check protocol
        has_valid_protocol = any(
            url.startswith(proto) for proto in VideoSourceValidator.SUPPORTED_PROTOCOLS
        )
        if not has_valid_protocol:
            result.add_error(
                f"Unsupported protocol (supported: {', '.join(VideoSourceValidator.SUPPORTED_PROTOCOLS)})"
            )
            result.add_suggestion(f"Provided URL: {url}")

        # Check accessibility
        if not source_info.is_accessible:
            result.add_error(source_info.error_message or "Cannot connect to stream")
            result.add_suggestion(
                "Check:\n"
                "  - URL is correct\n"
                "  - Internet connection is active\n"
                "  - Stream is online and not restricted\n"
                "  - Firewall allows access"
            )
            return result

        # Check metadata
        if not source_info.metadata:
            result.add_error("Cannot read stream metadata")
            return result

        if source_info.metadata.width <= 0 or source_info.metadata.height <= 0:
            result.add_warning("Stream resolution could not be determined")
            result.add_suggestion("Stream might still work despite this warning")

        # Check connection status
        connection_status = source_info.extra_info.get("connection_status", "unknown")
        if connection_status == "unstable":
            result.add_warning("Stream connection appears unstable")
            result.add_suggestion(
                "Analysis might be interrupted. Consider using a more stable connection"
            )

        return result

    @staticmethod
    def validate_webcam(source_info: VideoSourceInfo) -> ValidationResult:
        """Validate a webcam source.

        Args:
            source_info: VideoSourceInfo object for a webcam

        Returns:
            ValidationResult object
        """
        result = ValidationResult()

        if source_info.source_type != VideoSourceType.WEBCAM:
            result.add_error("Source is not a webcam")
            return result

        # Check accessibility
        if not source_info.is_accessible:
            result.add_error(source_info.error_message or "Cannot access webcam")
            result.add_suggestion(
                "Check:\n"
                "  - Webcam is connected\n"
                "  - Another application is not using it\n"
                "  - Application has permission to access webcam\n"
                "  - Try reconnecting the webcam"
            )
            return result

        # Check metadata
        if not source_info.metadata:
            result.add_error("Cannot read webcam metadata")
            return result

        if source_info.metadata.width <= 0 or source_info.metadata.height <= 0:
            result.add_error("Webcam resolution is invalid")
            result.add_suggestion("Try reconnecting the webcam")
            return result

        if source_info.metadata.fps <= 0:
            result.add_warning("Webcam FPS information is unavailable")

        # Low resolution warning
        if source_info.metadata.width < 640 or source_info.metadata.height < 480:
            result.add_warning(
                f"Low webcam resolution ({source_info.metadata.width}x{source_info.metadata.height})"
            )
            result.add_suggestion("Analysis might be less accurate with low resolution")

        return result

    @staticmethod
    def validate_source(source_info: VideoSourceInfo) -> ValidationResult:
        """Validate a video source.

        Args:
            source_info: VideoSourceInfo object

        Returns:
            ValidationResult object
        """
        if source_info.source_type == VideoSourceType.LOCAL_FILE:
            return VideoSourceValidator.validate_local_file(source_info)
        elif source_info.source_type == VideoSourceType.STREAMING_URL:
            return VideoSourceValidator.validate_streaming_url(source_info)
        elif source_info.source_type == VideoSourceType.WEBCAM:
            return VideoSourceValidator.validate_webcam(source_info)
        else:
            result = ValidationResult()
            result.add_error(f"Unknown source type: {source_info.source_type}")
            return result

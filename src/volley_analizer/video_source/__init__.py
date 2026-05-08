"""Video source management module."""

from .hardware_config import GPUBackend, HardwareConfig
from .manager import VideoMetadata, VideoSourceInfo, VideoSourceManager, VideoSourceType
from .ui_widget import FrameCaptureWorker, VideoSourceWidget
from .validator import ValidationResult, VideoSourceValidator

__all__ = [
    "VideoSourceManager",
    "VideoSourceType",
    "VideoSourceInfo",
    "VideoMetadata",
    "VideoSourceValidator",
    "ValidationResult",
    "HardwareConfig",
    "GPUBackend",
    "VideoSourceWidget",
    "FrameCaptureWorker",
]

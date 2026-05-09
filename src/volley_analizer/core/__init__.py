"""Volley Analyzer core modules."""

# Video acquisition system
# Frame buffering
from .frame_buffer import (
    AdaptiveBuffer,
    BufferMetrics,
    FrameBuffer,
    FrameBufferPool,
)

# Hardware decoder
from .hardware_decoder import (
    Codec,
    DecoderManager,
    DecoderPerformanceMetrics,
    DecoderType,
    HardwareDecoder,
    HardwareDecoderCapabilities,
    detect_codec_from_path,
    get_hardware_decoder,
)

# Video processing
from .video_processor import VideoMetadata, VideoProcessor
from .video_source import (
    VideoSource,
    VideoSourceFactory,
    VideoSourceInfo,
)

__all__ = [
    # Video source
    "VideoSource",
    "VideoSourceFactory",
    "VideoSourceInfo",
    # Hardware decoder
    "Codec",
    "DecoderType",
    "HardwareDecoder",
    "HardwareDecoderCapabilities",
    "DecoderPerformanceMetrics",
    "DecoderManager",
    "get_hardware_decoder",
    "detect_codec_from_path",
    # Frame buffer
    "BufferMetrics",
    "FrameBuffer",
    "FrameBufferPool",
    "AdaptiveBuffer",
    # Video processor
    "VideoProcessor",
    "VideoMetadata",
]

"""
Hardware decoder module with NVIDIA NVDEC support.

Features:
- NVIDIA NVDEC GPU acceleration
- Codec detection and optimization
- Performance monitoring
- Automatic fallback to software decoding
- Memory efficiency
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class Codec(Enum):
    """Supported video codecs."""

    H264 = "h264"
    H265 = "hevc"
    VP9 = "vp9"
    AV1 = "av1"
    MPEG2 = "mpeg2"
    UNKNOWN = "unknown"


class DecoderType(Enum):
    """Hardware decoder types."""

    NVIDIA_NVDEC = "nvidia_nvdec"
    INTEL_QUICKSYNC = "intel_quicksync"
    AMD_VCE = "amd_vce"
    SOFTWARE = "software"


@dataclass
class HardwareDecoderCapabilities:
    """Hardware decoder capabilities and specs."""

    decoder_type: DecoderType
    is_available: bool
    supported_codecs: list[Codec] = field(default_factory=list)
    max_resolution: tuple[int, int] = (4096, 2160)  # Default 4K
    max_fps: int = 120
    cuda_compute_capability: Optional[str] = None
    memory_mb: Optional[int] = None
    driver_version: Optional[str] = None
    device_index: int = 0

    def __str__(self) -> str:
        status = "✓ Available" if self.is_available else "✗ Not available"
        codecs = ", ".join([c.value.upper() for c in self.supported_codecs])
        info = f"{self.decoder_type.value} - {status}"
        if self.is_available:
            info += f"\n  Codecs: {codecs}"
            info += f"\n  Max: {self.max_resolution[0]}x{self.max_resolution[1]} @{self.max_fps}fps"
            if self.cuda_compute_capability:
                info += f"\n  CUDA CC: {self.cuda_compute_capability}"
            if self.memory_mb:
                info += f"\n  Memory: {self.memory_mb}MB"
        return info


@dataclass
class DecoderPerformanceMetrics:
    """Performance monitoring data."""

    frames_decoded: int = 0
    frames_failed: int = 0
    total_decode_time_ms: float = 0.0
    min_frame_time_ms: float = float("inf")
    max_frame_time_ms: float = 0.0
    avg_frame_time_ms: float = 0.0
    gpu_memory_used_mb: float = 0.0
    gpu_memory_peak_mb: float = 0.0
    fallback_to_cpu: bool = False

    @property
    def success_rate(self) -> float:
        """Calculate decode success rate."""
        total = self.frames_decoded + self.frames_failed
        return (self.frames_decoded / total * 100) if total > 0 else 0.0

    @property
    def avg_throughput_fps(self) -> float:
        """Calculate average throughput in FPS."""
        if self.total_decode_time_ms <= 0:
            return 0.0
        return self.frames_decoded / (self.total_decode_time_ms / 1000.0)

    def update(self, frame_decode_time_ms: float) -> None:
        """Update metrics with new frame decode time."""
        self.frames_decoded += 1
        self.total_decode_time_ms += frame_decode_time_ms
        self.min_frame_time_ms = min(self.min_frame_time_ms, frame_decode_time_ms)
        self.max_frame_time_ms = max(self.max_frame_time_ms, frame_decode_time_ms)
        self.avg_frame_time_ms = self.total_decode_time_ms / self.frames_decoded

    def __str__(self) -> str:
        return (
            f"Decoded: {self.frames_decoded} frames, "
            f"Failed: {self.frames_failed}, "
            f"Success rate: {self.success_rate:.1f}%, "
            f"Avg time: {self.avg_frame_time_ms:.2f}ms, "
            f"Throughput: {self.avg_throughput_fps:.1f} fps"
        )


class HardwareDecoder:
    """Main hardware decoder class with NVIDIA NVDEC support."""

    def __init__(self, enable_gpu: bool = True, device_index: int = 0) -> None:
        """
        Initialize hardware decoder.

        Args:
            enable_gpu: Enable GPU acceleration
            device_index: GPU device index for multi-GPU systems
        """
        self.enable_gpu = enable_gpu
        self.device_index = device_index
        self.current_decoder: Optional[DecoderType] = None
        self.metrics = DecoderPerformanceMetrics()
        self._capabilities: dict[DecoderType, HardwareDecoderCapabilities] = {}

        # Detect available decoders
        self._detect_decoders()

    def _detect_decoders(self) -> None:
        """Detect available hardware decoders."""
        # Detect NVIDIA NVDEC
        nvidia_caps = self._detect_nvidia_nvdec()
        self._capabilities[DecoderType.NVIDIA_NVDEC] = nvidia_caps

        # Detect Intel QuickSync (placeholder)
        # TODO: Implement Intel QSV detection

        # Detect AMD VCE (placeholder)
        # TODO: Implement AMD VCE detection

        # Software decoder always available
        self._capabilities[DecoderType.SOFTWARE] = HardwareDecoderCapabilities(
            decoder_type=DecoderType.SOFTWARE,
            is_available=True,
            supported_codecs=[Codec.H264, Codec.H265, Codec.VP9],
            max_fps=60,
        )

        logger.info("Hardware decoder detection complete")
        self._log_capabilities()

    def _detect_nvidia_nvdec(self) -> HardwareDecoderCapabilities:
        """Detect NVIDIA NVDEC availability and capabilities."""
        try:
            # Check nvidia-smi availability
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version,compute_cap",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                logger.debug("nvidia-smi not found or failed")
                return HardwareDecoderCapabilities(
                    decoder_type=DecoderType.NVIDIA_NVDEC,
                    is_available=False,
                )

            # Parse nvidia-smi output
            lines = result.stdout.strip().split("\n")
            if not lines or not lines[0]:
                logger.debug("No GPU output from nvidia-smi")
                return HardwareDecoderCapabilities(
                    decoder_type=DecoderType.NVIDIA_NVDEC,
                    is_available=False,
                )

            # Try to parse the first GPU
            try:
                parts = lines[0].split(",")
                gpu_name = parts[0].strip() if len(parts) > 0 else "Unknown"
                driver_version = parts[1].strip() if len(parts) > 1 else None
                compute_cap = parts[2].strip() if len(parts) > 2 else None
            except (IndexError, ValueError):
                gpu_name = "Unknown"
                driver_version = None
                compute_cap = None

            # Check ffmpeg for NVDEC support
            ffmpeg_supported = self._check_ffmpeg_nvdec()

            if not ffmpeg_supported:
                logger.debug("FFmpeg NVDEC support not detected")
                return HardwareDecoderCapabilities(
                    decoder_type=DecoderType.NVIDIA_NVDEC,
                    is_available=False,
                    driver_version=driver_version,
                )

            # Determine supported codecs based on compute capability
            supported_codecs = self._get_nvdec_supported_codecs(compute_cap)

            # Get GPU memory
            gpu_memory = self._get_gpu_memory()

            caps = HardwareDecoderCapabilities(
                decoder_type=DecoderType.NVIDIA_NVDEC,
                is_available=True,
                supported_codecs=supported_codecs,
                cuda_compute_capability=compute_cap,
                driver_version=driver_version,
                memory_mb=gpu_memory,
                device_index=self.device_index,
            )

            logger.info(f"NVIDIA GPU detected: {gpu_name}")
            return caps

        except subprocess.TimeoutExpired:
            logger.debug("nvidia-smi timeout")
            return HardwareDecoderCapabilities(
                decoder_type=DecoderType.NVIDIA_NVDEC,
                is_available=False,
            )
        except Exception as e:
            logger.debug(f"Error detecting NVIDIA NVDEC: {e}")
            return HardwareDecoderCapabilities(
                decoder_type=DecoderType.NVIDIA_NVDEC,
                is_available=False,
            )

    def _check_ffmpeg_nvdec(self) -> bool:
        """Check if FFmpeg has NVDEC support compiled."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-decoders"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Check for NVDEC decoders
            nvdec_decoders = ["h264_nvdec", "hevc_nvdec", "vp9_nvdec", "av1_nvdec"]
            output = result.stdout + result.stderr

            found = [dec for dec in nvdec_decoders if dec in output]
            if found:
                logger.debug(f"FFmpeg NVDEC decoders found: {found}")
                return True

            return False

        except Exception as e:
            logger.debug(f"Error checking FFmpeg NVDEC: {e}")
            return False

    def _get_nvdec_supported_codecs(self, compute_cap: Optional[str]) -> list[Codec]:
        """
        Get supported codecs based on CUDA compute capability.

        NVIDIA NVDEC support:
        - CC 3.0+: H.264, VP8, VP9 (limited)
        - CC 5.0+: H.264, VP8, VP9, HEVC
        - CC 6.1+: H.264, VP8, VP9, HEVC, AV1 (Maxwell+)
        - CC 7.0+: Full support (Volta+)
        """
        supported = [Codec.H264]  # H.264 is widely supported

        if compute_cap:
            try:
                major = int(compute_cap.split(".")[0])

                if major >= 5:
                    supported.extend([Codec.H265, Codec.VP9])
                elif major >= 3:
                    supported.append(Codec.VP9)

                if major >= 7:
                    supported.append(Codec.AV1)

            except (ValueError, IndexError):
                pass
        else:
            # Default to common codecs
            supported.extend([Codec.H265, Codec.VP9])

        return supported

    def _get_gpu_memory(self) -> Optional[int]:
        """Get total GPU memory in MB."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines and lines[0]:
                    return int(lines[0])

            return None

        except Exception:
            return None

    def get_best_decoder(self) -> DecoderType:
        """
        Get best available decoder.

        Priority:
        1. NVIDIA NVDEC (if enabled and available)
        2. Intel QuickSync (if available)
        3. AMD VCE (if available)
        4. Software decoder (always available)
        """
        if self.enable_gpu:
            if self._capabilities[DecoderType.NVIDIA_NVDEC].is_available:
                self.current_decoder = DecoderType.NVIDIA_NVDEC
                logger.info("Selected decoder: NVIDIA NVDEC")
                return DecoderType.NVIDIA_NVDEC

        # Fallback to software
        self.current_decoder = DecoderType.SOFTWARE
        logger.info("Selected decoder: Software")
        self.metrics.fallback_to_cpu = True
        return DecoderType.SOFTWARE

    def get_decoder_for_codec(self, codec: Codec) -> Optional[DecoderType]:
        """
        Get best decoder for specific codec.

        Args:
            codec: Video codec

        Returns:
            Best decoder type or None if codec not supported
        """
        if self.enable_gpu:
            nvidia_caps = self._capabilities.get(DecoderType.NVIDIA_NVDEC)
            if nvidia_caps and nvidia_caps.is_available:
                if codec in nvidia_caps.supported_codecs:
                    return DecoderType.NVIDIA_NVDEC

        # Check software decoder
        sw_caps = self._capabilities.get(DecoderType.SOFTWARE)
        if sw_caps and codec in sw_caps.supported_codecs:
            return DecoderType.SOFTWARE

        logger.warning(f"No decoder found for codec: {codec.value}")
        return None

    def get_capabilities(
        self, decoder_type: Optional[DecoderType] = None
    ) -> HardwareDecoderCapabilities | dict[DecoderType, HardwareDecoderCapabilities]:
        """
        Get decoder capabilities.

        Args:
            decoder_type: Specific decoder type, or None for all

        Returns:
            Single capability or dict of all capabilities
        """
        if decoder_type:
            return self._capabilities.get(decoder_type)
        return self._capabilities

    def _log_capabilities(self) -> None:
        """Log all detected decoder capabilities."""
        logger.info("=" * 60)
        logger.info("Hardware Decoder Capabilities")
        logger.info("=" * 60)
        for decoder_type, caps in self._capabilities.items():
            for line in str(caps).split("\n"):
                logger.info(f"  {line}")
        logger.info("=" * 60)

    def get_metrics(self) -> DecoderPerformanceMetrics:
        """Get performance metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = DecoderPerformanceMetrics()

    def log_metrics(self) -> None:
        """Log performance metrics."""
        logger.info(f"Decoder Metrics: {self.metrics}")


class DecoderManager:
    """Manages multiple decoder instances for different use cases."""

    def __init__(self) -> None:
        """Initialize decoder manager."""
        self._decoders: dict[str, HardwareDecoder] = {}
        self._default_decoder: Optional[HardwareDecoder] = None

    def create_decoder(
        self, name: str = "default", enable_gpu: bool = True
    ) -> HardwareDecoder:
        """Create a new hardware decoder instance."""
        decoder = HardwareDecoder(enable_gpu=enable_gpu)
        self._decoders[name] = decoder

        if name == "default" or self._default_decoder is None:
            self._default_decoder = decoder

        return decoder

    def get_decoder(self, name: str = "default") -> Optional[HardwareDecoder]:
        """Get decoder by name."""
        return self._decoders.get(name, self._default_decoder)

    def get_default_decoder(self) -> HardwareDecoder:
        """Get default decoder, creating if necessary."""
        if self._default_decoder is None:
            self.create_decoder("default")
        return self._default_decoder


# Global decoder manager instance
_decoder_manager = DecoderManager()


def get_hardware_decoder() -> HardwareDecoder:
    """
    Get the global hardware decoder instance.

    This is a convenience function for accessing the default decoder.
    """
    return _decoder_manager.get_default_decoder()


def detect_codec_from_path(file_path: str) -> Optional[Codec]:
    """
    Attempt to detect codec from file path using ffprobe.

    Args:
        file_path: Path to video file

    Returns:
        Detected codec or None
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "csv=p=0",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            codec_name = result.stdout.strip().lower()

            # Map codec names to Codec enum
            codec_map = {
                "h264": Codec.H264,
                "hevc": Codec.H265,
                "h265": Codec.H265,
                "vp9": Codec.VP9,
                "av1": Codec.AV1,
                "mpeg2video": Codec.MPEG2,
            }

            return codec_map.get(codec_name, Codec.UNKNOWN)

    except Exception as e:
        logger.debug(f"Error detecting codec: {e}")

    return None

"""Hardware acceleration configuration module."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import cv2


class GPUBackend(Enum):
    """GPU acceleration backends."""

    CUDA = "cuda"
    OPENCL = "opencl"
    NONE = "none"


@dataclass
class HardwareConfig:
    """Hardware acceleration configuration."""

    use_gpu: bool = False
    gpu_backend: GPUBackend = GPUBackend.NONE
    buffer_size: int = 30  # Frames to buffer
    frame_rate_adaptation: str = "auto"  # auto, low, medium, high
    max_gpu_memory_mb: Optional[int] = None

    @staticmethod
    def detect_gpu_support() -> dict:
        """Detect available GPU support on the system.

        Returns:
            Dictionary with GPU detection results
        """
        result = {
            "cuda_available": False,
            "opencl_available": False,
            "nvidia_gpu": None,
            "backends": [],
        }

        # Check for NVIDIA CUDA support
        try:
            # Try to use CUDA backend in OpenCV
            supported_backends = cv2.getBuildInformation()
            cuda_info = "CUDA" in supported_backends
            result["cuda_available"] = cuda_info

            if cuda_info:
                result["backends"].append("CUDA")
                result["nvidia_gpu"] = _get_nvidia_gpu_info()

        except Exception:
            pass

        # Check for OpenCL support
        try:
            opencl_available = cv2.ocl.haveOpenCL()
            result["opencl_available"] = opencl_available

            if opencl_available:
                result["backends"].append("OpenCL")

        except Exception:
            pass

        return result

    @staticmethod
    def create_default() -> HardwareConfig:
        """Create default hardware configuration.

        Returns:
            HardwareConfig with default values
        """
        gpu_support = HardwareConfig.detect_gpu_support()

        config = HardwareConfig()

        # Enable GPU if available (but default to False for stability)
        if gpu_support["cuda_available"]:
            config.gpu_backend = GPUBackend.CUDA
        elif gpu_support["opencl_available"]:
            config.gpu_backend = GPUBackend.OPENCL

        return config

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "use_gpu": self.use_gpu,
            "gpu_backend": self.gpu_backend.value,
            "buffer_size": self.buffer_size,
            "frame_rate_adaptation": self.frame_rate_adaptation,
            "max_gpu_memory_mb": self.max_gpu_memory_mb,
        }

    @classmethod
    def from_dict(cls, data: dict) -> HardwareConfig:
        """Create from dictionary representation."""
        return cls(
            use_gpu=data.get("use_gpu", False),
            gpu_backend=GPUBackend(data.get("gpu_backend", "none")),
            buffer_size=data.get("buffer_size", 30),
            frame_rate_adaptation=data.get("frame_rate_adaptation", "auto"),
            max_gpu_memory_mb=data.get("max_gpu_memory_mb"),
        )


def _get_nvidia_gpu_info() -> Optional[str]:
    """Get NVIDIA GPU information if available.

    Returns:
        GPU model string or None
    """
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            gpu_names = result.stdout.strip().split("\n")
            if gpu_names:
                return gpu_names[0]

    except Exception:
        pass

    return None

"""
Sistema di acquisizione video per Volley Analyzer.
Supporta: file locali, webcam, stream IP (RTSP/RTMP/HLS)
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VideoSourceInfo:
    """Informazioni base sulla sorgente video."""

    width: int
    height: int
    fps: float
    frame_count: int | None = None
    is_live: bool = False
    source_type: str = "unknown"

    @property
    def duration_seconds(self) -> float | None:
        if self.frame_count and self.fps and self.fps > 0:
            return self.frame_count / self.fps
        return None


class VideoSource(ABC):
    """Interfaccia base per sorgenti video."""

    @abstractmethod
    def open(self) -> bool:
        """Apre la sorgente video."""
        pass

    @abstractmethod
    def read(self) -> tuple[bool, np.ndarray | None]:
        """Legge un frame. Ritorna (successo, frame)."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Rilascia le risorse."""
        pass

    @abstractmethod
    def get_info(self) -> VideoSourceInfo | None:
        """Ritorna informazioni sulla sorgente."""
        pass

    @property
    @abstractmethod
    def is_opened(self) -> bool:
        """Vero se la sorgente è aperta e funzionante."""
        pass


class OpenCVSource(VideoSource):
    """Implementazione base usando cv2.VideoCapture."""

    def __init__(self, source_path: str | int, use_hw_accel: bool = True):
        self.source_path = source_path
        self.use_hw_accel = use_hw_accel
        self.cap: cv2.VideoCapture | None = None
        self._info: VideoSourceInfo | None = None
        self._is_live = False
        self._source_type = self._detect_type(source_path)

    def _detect_type(self, source_path: str | int) -> str:
        if isinstance(source_path, int):
            self._is_live = True
            return "webcam"

        path_str = str(source_path).lower()
        if path_str.startswith(("rtsp://", "rtmp://", "http://", "https://")):
            self._is_live = True
            return "stream"

        return "file"

    def _configure_hw_accel(self) -> int:
        """Configura l'API backend per l'accelerazione hardware se richiesta."""
        api_preference = cv2.CAP_ANY

        if not self.use_hw_accel:
            return api_preference

        # Tenta di usare FFmpeg con accelerazione hardware
        # In OpenCV compilato con supporto CUDA/NVDEC
        return cv2.CAP_FFMPEG

    def open(self) -> bool:
        try:
            api_pref = self._configure_hw_accel()

            # Se è uno stream di rete, ottimizziamo i buffer
            if self._is_live and isinstance(self.source_path, str):
                # Usiamo ENV vars per FFmpeg (che OpenCV usa sotto il cofano)
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtsp_transport;tcp|analyzeduration;500000|probesize;5000000"
                )

            self.cap = cv2.VideoCapture(self.source_path, api_pref)

            if not self.cap.isOpened():
                logger.error(f"Impossibile aprire la sorgente: {self.source_path}")
                return False

            # Estrai informazioni
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(self.cap.get(cv2.CAP_PROP_FPS))

            # Se FPS non è valido, usa default ragionevole
            if fps <= 0 or np.isnan(fps):
                fps = 25.0

            frame_count = None
            if not self._is_live:
                count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if count > 0:
                    frame_count = count

            self._info = VideoSourceInfo(
                width=width,
                height=height,
                fps=fps,
                frame_count=frame_count,
                is_live=self._is_live,
                source_type=self._source_type,
            )

            logger.info(
                f"Sorgente aperta ({self._source_type}): {width}x{height} @ {fps}fps"
            )
            return True

        except Exception as e:
            logger.error(f"Errore apertura sorgente {self.source_path}: {e}")
            return False

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self.is_opened:
            return False, None

        return self.cap.read()

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def get_info(self) -> VideoSourceInfo | None:
        return self._info

    @property
    def is_opened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()


class VideoSourceFactory:
    """Factory per creare la giusta sorgente video."""

    @staticmethod
    def create(source_path: str | int, use_hw_accel: bool = True) -> VideoSource:
        """
        Crea e istanzia una VideoSource.

        Args:
            source_path: Path al file, URL RTSP/RTMP, o ID webcam (0, 1, 2)
            use_hw_accel: Se tentare di usare NVDEC/accelerazione hardware
        """
        # Per ora usiamo OpenCVSource per tutto.
        # In futuro si può aggiungere un FFmpegSource nativo via subprocess per NVDEC puro.
        source = OpenCVSource(source_path, use_hw_accel)
        return source

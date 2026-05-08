"""
Integrazione di VideoSource nel VideoProcessor esistente.
Mantiene la retrocompatibilità con la vecchia API di VideoProcessor,
ma usa internamente il nuovo sistema flessibile.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterator

import cv2
import numpy as np

from .video_source import VideoSourceFactory, VideoSourceInfo

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Metadata compatibile con la vecchia API."""

    width: int
    height: int
    fps: float
    frame_count: int | None

    @property
    def duration_seconds(self) -> float | None:
        if self.frame_count and self.fps and self.fps > 0:
            return self.frame_count / self.fps
        return None


class VideoProcessor:
    """
    Gestisce la lettura dei video o stream usando il nuovo VideoSource backend.
    """

    def __init__(
        self,
        video_path: str | int,
        sample_every_n_frames: int = 1,
        use_hw_accel: bool = True,
    ) -> None:
        """
        Inizializza il processor.

        Args:
            video_path: Path al file, URL RTSP/RTMP o ID webcam
            sample_every_n_frames: Processa un frame ogni N
            use_hw_accel: Usa accelerazione GPU se disponibile
        """
        self.source = VideoSourceFactory.create(video_path, use_hw_accel)

        if not self.source.open():
            raise RuntimeError(f"Impossibile aprire la sorgente video: {video_path}")

        info = self.source.get_info()
        self.metadata = VideoMetadata(
            width=info.width,
            height=info.height,
            fps=info.fps,
            frame_count=info.frame_count,
        )
        self.sample_every_n_frames = max(1, sample_every_n_frames)
        self.is_live = info.is_live

    def frames(self) -> Iterator[tuple[int, float, np.ndarray]]:
        """
        Genera i frame dal video.

        Yields:
            (frame_idx, timestamp_sec, frame)
        """
        frame_idx = 0

        while self.source.is_opened:
            ret, frame = self.source.read()
            if not ret or frame is None:
                break

            # Skip frame se necessario
            if frame_idx % self.sample_every_n_frames == 0:
                # Per live stream, usiamo il frame_idx come approssimazione del tempo
                # Per file locali, possiamo essere più precisi
                timestamp = (
                    frame_idx / self.metadata.fps if self.metadata.fps > 0 else 0.0
                )
                yield frame_idx, timestamp, frame

            frame_idx += 1

    def release(self) -> None:
        """Rilascia le risorse."""
        if self.source:
            self.source.release()

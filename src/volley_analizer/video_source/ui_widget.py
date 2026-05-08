"""Video source widget for GUI."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np

try:
    from PyQt6.QtCore import QRect, Qt, QThread, QTimer, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
    from PyQt6.QtWidgets import (
        QButtonGroup,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:
    raise RuntimeError("PyQt6 non installato") from exc

from .manager import VideoSourceInfo, VideoSourceManager, VideoSourceType
from .validator import VideoSourceValidator


class FrameCaptureWorker(QThread):
    """Worker thread for capturing frames from video source."""

    frame_captured = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)

    def __init__(self, source_info: VideoSourceInfo) -> None:
        """Initialize frame capture worker."""
        super().__init__()
        self.source_info = source_info
        self._stop = False

    def run(self) -> None:
        """Run the frame capture."""
        try:
            manager = VideoSourceManager()
            frame = manager.capture_first_frame(self.source_info)

            if frame is not None:
                self.frame_captured.emit(frame)
            else:
                self.error_occurred.emit("Could not capture frame")

        except Exception as exc:
            self.error_occurred.emit(str(exc))

    def stop(self) -> None:
        """Stop the capture worker."""
        self._stop = True


class VideoSourceWidget(QWidget):
    """Widget for selecting and configuring video sources."""

    source_changed = pyqtSignal(VideoSourceInfo)
    validation_updated = pyqtSignal(dict)

    def __init__(self) -> None:
        """Initialize the video source widget."""
        super().__init__()
        self.manager = VideoSourceManager()
        self.validator = VideoSourceValidator()
        self.current_source: Optional[VideoSourceInfo] = None
        self.frame_worker: Optional[FrameCaptureWorker] = None

        self._build_ui()
        self._update_webcam_list()

    def _build_ui(self) -> None:
        """Build the UI."""
        layout = QVBoxLayout(self)

        # === Source Type Selection ===
        type_group = QGroupBox("Sorgente Video")
        type_layout = QHBoxLayout()

        self.source_group = QButtonGroup()
        self.file_radio = QRadioButton("File Locale")
        self.stream_radio = QRadioButton("Streaming URL")
        self.webcam_radio = QRadioButton("Webcam")

        self.source_group.addButton(self.file_radio, 0)
        self.source_group.addButton(self.stream_radio, 1)
        self.source_group.addButton(self.webcam_radio, 2)

        self.file_radio.setChecked(True)
        self.file_radio.toggled.connect(self._on_source_type_changed)
        self.stream_radio.toggled.connect(self._on_source_type_changed)
        self.webcam_radio.toggled.connect(self._on_source_type_changed)

        type_layout.addWidget(self.file_radio)
        type_layout.addWidget(self.stream_radio)
        type_layout.addWidget(self.webcam_radio)
        type_layout.addStretch()

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # === Source Input Controls ===
        input_group = QGroupBox("Configurazione Sorgente")
        input_layout = QVBoxLayout()

        # File input row
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Path del video locale...")
        self.file_input.setVisible(True)
        browse_btn = QPushButton("Sfoglia...")
        browse_btn.clicked.connect(self._on_browse_file)
        browse_btn.setMaximumWidth(100)

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("File:"))
        file_row.addWidget(self.file_input)
        file_row.addWidget(browse_btn)

        # URL input row
        self.stream_input = QLineEdit()
        self.stream_input.setPlaceholderText("http://... o rtsp://...")
        self.stream_input.setVisible(False)

        stream_row = QHBoxLayout()
        stream_row.addWidget(QLabel("URL:"))
        stream_row.addWidget(self.stream_input)

        # Webcam selection row
        self.webcam_combo = QComboBox()
        self.webcam_combo.setVisible(False)
        refresh_webcams_btn = QPushButton("Aggiorna")
        refresh_webcams_btn.setMaximumWidth(100)
        refresh_webcams_btn.clicked.connect(self._update_webcam_list)

        webcam_row = QHBoxLayout()
        webcam_row.addWidget(QLabel("Webcam:"))
        webcam_row.addWidget(self.webcam_combo)
        webcam_row.addWidget(refresh_webcams_btn)
        webcam_row.addStretch()

        input_layout.addLayout(file_row)
        input_layout.addLayout(stream_row)
        input_layout.addLayout(webcam_row)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # === Drag & Drop Area ===
        self.drag_drop_label = QLabel("📁 Trascina un video qui")
        self.drag_drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_drop_label.setStyleSheet(
            "border: 2px dashed #999; border-radius: 4px; padding: 30px; "
            "background-color: #f5f5f5;"
        )
        self.drag_drop_label.setMinimumHeight(60)
        self.setAcceptDrops(True)
        layout.addWidget(self.drag_drop_label)

        # === Preview Section ===
        preview_group = QGroupBox("Anteprima")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(320, 180)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "border: 1px solid #ccc; background-color: #000;"
        )

        preview_layout.addWidget(self.preview_label)

        # Metadata display
        metadata_layout = QFormLayout()
        self.resolution_label = QLabel("--")
        self.fps_label = QLabel("--")
        self.duration_label = QLabel("--")
        self.codec_label = QLabel("--")

        metadata_layout.addRow("Risoluzione:", self.resolution_label)
        metadata_layout.addRow("FPS:", self.fps_label)
        metadata_layout.addRow("Durata:", self.duration_label)
        metadata_layout.addRow("Codec:", self.codec_label)

        preview_layout.addLayout(metadata_layout)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # === Validation Messages ===
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("color: #d32f2f; padding: 5px;")
        layout.addWidget(self.validation_label)

        # === Hardware Configuration ===
        hw_group = QGroupBox("Configurazione Hardware")
        hw_layout = QFormLayout()

        self.gpu_checkbox = QCheckBox("Usa Accelerazione GPU")
        hw_layout.addRow(self.gpu_checkbox)

        self.buffer_spin = QSpinBox()
        self.buffer_spin.setRange(5, 100)
        self.buffer_spin.setValue(30)
        hw_layout.addRow("Buffer Size (frame):", self.buffer_spin)

        self.adaptation_combo = QComboBox()
        self.adaptation_combo.addItems(["Auto", "Basso", "Medio", "Alto"])
        hw_layout.addRow("Adattamento Frame Rate:", self.adaptation_combo)

        hw_group.setLayout(hw_layout)
        layout.addWidget(hw_group)

        # === Action Buttons ===
        button_layout = QHBoxLayout()
        validate_btn = QPushButton("Valida Sorgente")
        validate_btn.clicked.connect(self._validate_current_source)

        self.confirm_btn = QPushButton("Conferma")
        self.confirm_btn.clicked.connect(self._confirm_source)
        self.confirm_btn.setEnabled(False)

        button_layout.addWidget(validate_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.confirm_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

        # Update GPU status
        self._update_gpu_status()

    def _on_source_type_changed(self) -> None:
        """Handle source type change."""
        if self.file_radio.isChecked():
            self.file_input.setVisible(True)
            self.stream_input.setVisible(False)
            self.webcam_combo.setVisible(False)
            self.drag_drop_label.setVisible(True)
        elif self.stream_radio.isChecked():
            self.file_input.setVisible(False)
            self.stream_input.setVisible(True)
            self.webcam_combo.setVisible(False)
            self.drag_drop_label.setVisible(False)
        elif self.webcam_radio.isChecked():
            self.file_input.setVisible(False)
            self.stream_input.setVisible(False)
            self.webcam_combo.setVisible(True)
            self.drag_drop_label.setVisible(False)

        self._clear_preview()

    def _on_browse_file(self) -> None:
        """Handle file browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;All Files (*)",
        )

        if file_path:
            self.file_input.setText(file_path)
            self._on_source_input_changed()

    def _on_source_input_changed(self) -> None:
        """Handle source input change."""
        self._auto_detect_source()
        self._validate_current_source()

    def _auto_detect_source(self) -> None:
        """Auto-detect and validate the current source."""
        try:
            if self.file_radio.isChecked():
                path = self.file_input.text().strip()
                if path:
                    source_info = self.manager.get_local_file_info(path)
                else:
                    self._clear_preview()
                    return

            elif self.stream_radio.isChecked():
                url = self.stream_input.text().strip()
                if url:
                    source_info = self.manager.get_streaming_info(url)
                else:
                    self._clear_preview()
                    return

            elif self.webcam_radio.isChecked():
                index = self.webcam_combo.currentData()
                if index is not None:
                    source_info = self.manager.get_webcam_info(index)
                else:
                    self._clear_preview()
                    return
            else:
                return

            self.current_source = source_info
            self._update_preview()

        except Exception as exc:
            self.validation_label.setText(f"Errore: {str(exc)}")
            self._clear_preview()

    def _update_preview(self) -> None:
        """Update the preview with metadata."""
        if not self.current_source or not self.current_source.metadata:
            self._clear_preview()
            return

        # Update metadata labels
        metadata = self.current_source.metadata
        self.resolution_label.setText(f"{metadata.width}x{metadata.height}")
        self.fps_label.setText(f"{metadata.fps:.1f}")

        if metadata.is_streaming:
            self.duration_label.setText("Live")
        elif metadata.duration_seconds:
            mins = int(metadata.duration_seconds) // 60
            secs = int(metadata.duration_seconds) % 60
            self.duration_label.setText(f"{mins}m {secs}s")
        else:
            self.duration_label.setText("--")

        # Get codec info
        codec_info = self.manager.validate_codec_support(self.current_source)
        self.codec_label.setText(codec_info.get("codec", "unknown"))

        # Capture and display first frame
        if self.frame_worker:
            self.frame_worker.wait()

        self.frame_worker = FrameCaptureWorker(self.current_source)
        self.frame_worker.frame_captured.connect(self._on_frame_captured)
        self.frame_worker.error_occurred.connect(self._on_frame_error)
        self.frame_worker.start()

    def _on_frame_captured(self, frame: np.ndarray) -> None:
        """Handle captured frame."""
        # Resize frame to fit preview
        h, w = frame.shape[:2]
        max_w, max_h = 320, 180
        scale = min(max_w / w, max_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h))

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to QPixmap
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(
            frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qt_image)

        self.preview_label.setPixmap(pixmap)

    def _on_frame_error(self, error: str) -> None:
        """Handle frame capture error."""
        self.preview_label.setText(f"Errore: {error}")

    def _clear_preview(self) -> None:
        """Clear the preview."""
        self.preview_label.clear()
        self.preview_label.setText("--")
        self.resolution_label.setText("--")
        self.fps_label.setText("--")
        self.duration_label.setText("--")
        self.codec_label.setText("--")
        self.validation_label.clear()
        self.confirm_btn.setEnabled(False)

    def _validate_current_source(self) -> None:
        """Validate the current source."""
        self._auto_detect_source()

        if not self.current_source:
            self.validation_label.setText("❌ Seleziona una sorgente")
            self.confirm_btn.setEnabled(False)
            return

        result = self.validator.validate_source(self.current_source)

        # Build validation message
        message_parts = []

        if result.is_valid:
            message_parts.append("✓ Sorgente valida")
        else:
            message_parts.append("❌ Errori di validazione:")
            message_parts.extend([f"  - {e}" for e in result.errors])

        if result.warnings:
            message_parts.append("\n⚠ Avvisi:")
            message_parts.extend([f"  - {w}" for w in result.warnings])

        if result.suggestions:
            message_parts.append("\n💡 Suggerimenti:")
            message_parts.extend([f"  - {s}" for s in result.suggestions])

        message = "\n".join(message_parts)
        self.validation_label.setText(message)

        # Color coding
        if result.is_valid:
            self.validation_label.setStyleSheet("color: #2e7d32; padding: 5px;")
        else:
            self.validation_label.setStyleSheet("color: #d32f2f; padding: 5px;")

        self.confirm_btn.setEnabled(result.is_valid)
        self.validation_updated.emit(result.to_dict())

    def _confirm_source(self) -> None:
        """Confirm the current source."""
        if self.current_source and self.current_source.is_accessible:
            self.manager.set_current_source(self.current_source)
            self.source_changed.emit(self.current_source)

    def _update_webcam_list(self) -> None:
        """Update the webcam list."""
        webcams = self.manager.detect_webcams()
        self.webcam_combo.clear()

        if not webcams:
            self.webcam_combo.addItem("Nessuna webcam trovata", None)
            self.webcam_combo.setEnabled(False)
        else:
            for webcam in webcams:
                display_text = f"{webcam['name']} - {webcam['resolution']} @ {webcam['fps']:.0f}fps"
                self.webcam_combo.addItem(display_text, webcam["index"])
            self.webcam_combo.setEnabled(True)

    def _update_gpu_status(self) -> None:
        """Update GPU status."""
        from .hardware_config import HardwareConfig

        gpu_support = HardwareConfig.detect_gpu_support()

        if gpu_support["cuda_available"]:
            gpu_name = gpu_support.get("nvidia_gpu", "NVIDIA GPU")
            self.gpu_checkbox.setText(f"Usa Accelerazione GPU ({gpu_name})")
            self.gpu_checkbox.setEnabled(True)
        elif gpu_support["opencl_available"]:
            self.gpu_checkbox.setText("Usa Accelerazione GPU (OpenCL)")
            self.gpu_checkbox.setEnabled(True)
        else:
            self.gpu_checkbox.setText("GPU non disponibile")
            self.gpu_checkbox.setEnabled(False)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drag_drop_label.setStyleSheet(
                "border: 2px dashed #2196F3; border-radius: 4px; padding: 30px; "
                "background-color: #e3f2fd;"
            )

    def dragLeaveEvent(self, event) -> None:
        """Handle drag leave event."""
        self.drag_drop_label.setStyleSheet(
            "border: 2px dashed #999; border-radius: 4px; padding: 30px; "
            "background-color: #f5f5f5;"
        )

    def dropEvent(self, event) -> None:
        """Handle drop event."""
        self.drag_drop_label.setStyleSheet(
            "border: 2px dashed #999; border-radius: 4px; padding: 30px; "
            "background-color: #f5f5f5;"
        )

        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.file_input.setText(file_path)
            self._on_source_input_changed()
            event.acceptProposedAction()

    def get_current_source(self) -> Optional[VideoSourceInfo]:
        """Get the current selected source."""
        return self.current_source

    def get_hardware_config(self):
        """Get the current hardware configuration."""
        from .hardware_config import HardwareConfig

        config = HardwareConfig()
        config.use_gpu = self.gpu_checkbox.isChecked() and self.gpu_checkbox.isEnabled()
        config.buffer_size = self.buffer_spin.value()
        adaptation_map = {
            "Auto": "auto",
            "Basso": "low",
            "Medio": "medium",
            "Alto": "high",
        }
        config.frame_rate_adaptation = adaptation_map.get(
            self.adaptation_combo.currentText(), "auto"
        )

        return config

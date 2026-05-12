from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

try:
    import cv2
except Exception:
    cv2 = None


class VideoPlayer(QWidget):
    """Player video con sorgenti file/webcam/IP e preview live."""

    source_changed = pyqtSignal(dict)
    playback_position_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_source = None
        self.capture = None
        self.last_frame = None
        self.frame_interval_seconds = 1.0 / 30.0
        self.stream_elapsed_seconds = 0.0
        self.pending_resume_seconds: float | None = None

        self.recording_enabled = False
        self.video_writer = None
        self.recording_output_path: str | None = None
        self.recording_frame_size: tuple[int, int] | None = None

        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self._read_next_frame)

        self._setup_ui()
        self._on_source_type_changed()
        self._update_record_button_state()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Video")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Sorgente:"))

        self.source_type = QComboBox()
        self.source_type.addItem("Video salvato", "file")
        self.source_type.addItem("Webcam locale", "webcam")
        self.source_type.addItem("Stream IP", "ip")
        self.source_type.currentIndexChanged.connect(self._on_source_type_changed)
        source_row.addWidget(self.source_type)

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Seleziona un file video")
        source_row.addWidget(self.source_input, 1)

        self.btn_browse = QPushButton("Sfoglia")
        self.btn_browse.clicked.connect(self._browse_file)
        source_row.addWidget(self.btn_browse)

        layout.addLayout(source_row)

        controls_row = QHBoxLayout()
        self.btn_connect = QPushButton("Connetti")
        self.btn_connect.clicked.connect(self._connect_source)
        controls_row.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Disconnetti")
        self.btn_disconnect.clicked.connect(self._disconnect_source)
        self.btn_disconnect.setEnabled(False)
        controls_row.addWidget(self.btn_disconnect)

        self.btn_record = QPushButton("Inizia registrazione")
        self.btn_record.clicked.connect(self._toggle_recording)
        self.btn_record.setEnabled(False)
        controls_row.addWidget(self.btn_record)

        controls_row.addStretch()
        layout.addLayout(controls_row)

        self.preview_label = QLabel("Anteprima video non ancora disponibile")
        self.preview_label.setMinimumHeight(320)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "border: 1px solid #6E4B32; border-radius: 8px; padding: 8px;"
        )
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label, 1)

        self.status_label = QLabel("Stato: inattivo")
        layout.addWidget(self.status_label)

    def _on_source_type_changed(self):
        source_kind = self.source_type.currentData()
        if source_kind == "file":
            self.source_input.setPlaceholderText("Seleziona un file video")
            self.btn_browse.setEnabled(True)
        elif source_kind == "webcam":
            self.source_input.setPlaceholderText("Indice webcam (es: 0)")
            self.btn_browse.setEnabled(False)
            if not self.source_input.text().strip():
                self.source_input.setText("0")
        else:
            self.source_input.setPlaceholderText("URL stream IP (rtsp/http)")
            self.btn_browse.setEnabled(False)

        self._update_record_button_state()

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona video",
            "",
            "Video (*.mp4 *.avi *.mov *.mkv *.m4v);;Tutti i file (*)",
        )
        if file_path:
            self.source_input.setText(file_path)

    def _build_capture_source(self, source_kind: str, source_value: str):
        if source_kind == "webcam":
            try:
                return int(source_value)
            except ValueError:
                return source_value
        return source_value

    def _recordings_dir(self) -> Path:
        target = Path.home() / "VolleyballScoutRecordings"
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _can_record_live_source(self) -> bool:
        source_kind = (self.current_source or {}).get("type")
        return bool(
            cv2 is not None
            and self.capture is not None
            and source_kind in {"webcam", "ip"}
        )

    def _update_record_button_state(self):
        if not hasattr(self, "btn_record"):
            return

        can_record = self._can_record_live_source()
        self.btn_record.setEnabled(can_record or self.recording_enabled)
        self.btn_record.setText(
            "Stop registrazione" if self.recording_enabled else "Inizia registrazione"
        )

    def _emit_source_changed(self):
        payload = dict(self.current_source or {})
        if self.recording_output_path:
            payload["recorded_path"] = self.recording_output_path
        payload["recording"] = bool(self.recording_enabled)
        self.source_changed.emit(payload)

    def _toggle_recording(self):
        if self.recording_enabled:
            self._stop_recording(silent=False)
        else:
            self._start_recording()

    def _start_recording(self):
        if cv2 is None:
            return
        if not self._can_record_live_source():
            QMessageBox.information(
                self,
                "Registrazione non disponibile",
                "La registrazione è disponibile solo per webcam locale o stream IP connessi.",
            )
            return

        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if (width <= 0 or height <= 0) and self.last_frame is not None:
            try:
                height, width = self.last_frame.shape[:2]
            except Exception:
                width, height = 0, 0

        if width <= 0 or height <= 0:
            QMessageBox.warning(
                self,
                "Dimensioni video non valide",
                "Impossibile determinare la risoluzione della sorgente.",
            )
            return

        fps = float(self.capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 1.0 or fps > 120.0:
            fps = 30.0

        source_kind = str((self.current_source or {}).get("type") or "live")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self._recordings_dir() / f"scout_{source_kind}_{stamp}.mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            str(output_path), fourcc, fps, (int(width), int(height))
        )
        if writer is None or not writer.isOpened():
            QMessageBox.warning(
                self,
                "Errore registrazione",
                "Impossibile iniziare la registrazione locale del video.",
            )
            return

        self.video_writer = writer
        self.recording_frame_size = (int(width), int(height))
        self.recording_output_path = str(output_path)
        self.recording_enabled = True

        # Sincronizza il tempo scouting al nuovo video registrato (t=0)
        self.stream_elapsed_seconds = 0.0
        self.pending_resume_seconds = 0.0
        self.playback_position_changed.emit(0.0)

        source_kind_text = str((self.current_source or {}).get("type") or "live")
        self.status_label.setText(f"Stato: connesso ({source_kind_text}) • REC")
        self._update_record_button_state()
        self._emit_source_changed()

    def _stop_recording(self, silent: bool = False):
        if self.video_writer is not None:
            try:
                self.video_writer.release()
            except Exception:
                pass

        was_recording = self.recording_enabled
        self.video_writer = None
        self.recording_frame_size = None
        self.recording_enabled = False

        source_kind = str((self.current_source or {}).get("type") or "")
        if self.capture is not None:
            if self.recording_output_path and was_recording:
                self.status_label.setText(
                    f"Stato: connesso ({source_kind}) • registrazione salvata"
                )
            else:
                self.status_label.setText(f"Stato: connesso ({source_kind})")

        self._update_record_button_state()
        if was_recording and not silent:
            self._emit_source_changed()

    def connect_current_source(self, force_reconnect: bool = False) -> bool:
        """Connette la sorgente attualmente impostata nei controlli."""
        source_kind = self.source_type.currentData()
        source_value = self.source_input.text().strip()

        if not force_reconnect and self.capture is not None and self.current_source:
            if (
                str(self.current_source.get("type") or "") == str(source_kind or "")
                and str(self.current_source.get("value") or "") == source_value
            ):
                return True

        self._connect_source()
        return self.capture is not None

    def set_resume_position(self, seconds: float | None):
        """Imposta/aggiorna il punto di ripartenza in secondi."""
        if seconds is None:
            return

        try:
            target = max(0.0, float(seconds))
        except Exception:
            return

        self.pending_resume_seconds = target

        source_kind = (self.current_source or {}).get("type")
        if self.capture is not None and source_kind == "file":
            self.capture.set(cv2.CAP_PROP_POS_MSEC, target * 1000.0)
            self.stream_elapsed_seconds = target
            self._read_next_frame()

    def _connect_source(self):
        if cv2 is None:
            QMessageBox.critical(
                self,
                "OpenCV non disponibile",
                "Modulo cv2 non trovato. Installa opencv-python nell'ambiente corrente.",
            )
            return

        source_kind = self.source_type.currentData()
        source_value = self.source_input.text().strip()

        if not source_value:
            QMessageBox.warning(
                self, "Sorgente mancante", "Inserisci una sorgente video valida."
            )
            return

        if source_kind == "file":
            path = Path(source_value)
            if not path.exists():
                QMessageBox.warning(
                    self,
                    "File non trovato",
                    f"Il file selezionato non esiste:\n{source_value}",
                )
                return

        self._disconnect_source(silent=True)

        self.recording_output_path = None

        cap_source = self._build_capture_source(source_kind, source_value)
        capture = cv2.VideoCapture(cap_source)

        if capture is None or not capture.isOpened():
            if capture is not None:
                capture.release()
            QMessageBox.warning(
                self,
                "Connessione fallita",
                "Impossibile aprire la sorgente video selezionata.",
            )
            return

        self.capture = capture
        self.current_source = {"type": source_kind, "value": source_value}

        fps = float(self.capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 1.0 or fps > 120.0:
            fps = 30.0
        interval_ms = max(15, int(1000.0 / fps))
        self.frame_interval_seconds = interval_ms / 1000.0
        self.stream_elapsed_seconds = 0.0

        if source_kind == "file" and self.pending_resume_seconds is not None:
            try:
                target = max(0.0, float(self.pending_resume_seconds))
                self.capture.set(cv2.CAP_PROP_POS_MSEC, target * 1000.0)
                self.stream_elapsed_seconds = target
            except Exception:
                pass

        self.frame_timer.start(interval_ms)
        self._read_next_frame()

        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(True)
        self.status_label.setText(f"Stato: connesso ({source_kind})")

        self._update_record_button_state()
        self._emit_source_changed()

    def _read_next_frame(self):
        if cv2 is None or self.capture is None:
            return

        source_kind = (self.current_source or {}).get("type")
        ok, frame = self.capture.read()
        if not ok or frame is None:
            source_kind = (self.current_source or {}).get("type")

            if source_kind == "file":
                self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self.capture.read()
                if not ok or frame is None:
                    self.status_label.setText("Stato: stream terminato")
                    return
            else:
                self.status_label.setText(
                    f"Stato: connesso ({source_kind}) - nessun frame"
                )
                return

        if self.recording_enabled and self.video_writer is not None:
            frame_to_save = frame
            if self.recording_frame_size is not None:
                rec_w, rec_h = self.recording_frame_size
                if frame.shape[1] != rec_w or frame.shape[0] != rec_h:
                    frame_to_save = cv2.resize(frame, (rec_w, rec_h))
            try:
                self.video_writer.write(frame_to_save)
            except Exception:
                pass

        current_seconds = 0.0
        if source_kind == "file":
            current_seconds = (
                float(self.capture.get(cv2.CAP_PROP_POS_MSEC) or 0.0) / 1000.0
            )
            if current_seconds <= 0.0:
                current_seconds = self.stream_elapsed_seconds
        else:
            self.stream_elapsed_seconds += self.frame_interval_seconds
            current_seconds = self.stream_elapsed_seconds

        self.last_frame = frame
        self._render_frame(frame)
        self.playback_position_changed.emit(max(0.0, float(current_seconds)))

    def _render_frame(self, frame):
        if cv2 is None or frame is None:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = rgb_frame.shape
        bytes_per_line = c * w

        image = QImage(
            rgb_frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()

        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def _disconnect_source(self, silent: bool = False):
        self.frame_timer.stop()

        if self.recording_enabled:
            self._stop_recording(silent=silent)

        if self.capture is not None:
            try:
                self.capture.release()
            except Exception:
                pass
        self.capture = None
        self.current_source = None
        self.last_frame = None
        self.stream_elapsed_seconds = 0.0

        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self._update_record_button_state()
        self.status_label.setText("Stato: inattivo")
        self.preview_label.clear()
        self.preview_label.setText("Anteprima video non ancora disponibile")

        if not silent:
            payload = {"type": None, "value": None, "recording": False}
            if self.recording_output_path:
                payload["recorded_path"] = self.recording_output_path
            self.source_changed.emit(payload)
            self.playback_position_changed.emit(0.0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.last_frame is not None:
            self._render_frame(self.last_frame)

    def closeEvent(self, event):
        self._disconnect_source(silent=True)
        super().closeEvent(event)

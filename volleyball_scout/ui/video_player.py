from __future__ import annotations

import time
from collections import deque
from datetime import datetime
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Lock

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

try:
    import cv2
except Exception:
    cv2 = None


class CaptureWorker(QThread):
    """Acquisizione frame in thread separato con supporto seek per file."""

    frame_captured = pyqtSignal(object, float, float, str)
    capture_warning = pyqtSignal(str)

    def __init__(
        self,
        capture,
        source_kind: str,
        frame_interval_seconds: float,
        *,
        parent=None,
    ):
        """Inizializza worker acquisizione frame."""
        super().__init__(parent)
        self.capture = capture
        self.source_kind = str(source_kind or "")
        self.frame_interval_seconds = float(max(0.001, frame_interval_seconds))

        self._stop_requested = False
        self._warning_emitted = False
        self._stream_elapsed_seconds = 0.0
        self._lock = Lock()
        self._seek_seconds: float | None = None
        self._paused = False

    def request_stop(self):
        """Richiede arresto worker."""
        with self._lock:
            self._stop_requested = True

    def request_seek(self, seconds: float):
        """Richiede seek a un secondo specifico."""
        if self.source_kind != "file":
            return
        with self._lock:
            self._seek_seconds = max(0.0, float(seconds))

    def request_pause(self, paused: bool):
        """Richiede pausa/ripresa riproduzione."""
        if self.source_kind != "file":
            return
        with self._lock:
            self._paused = bool(paused)

    def _consume_seek(self) -> float | None:
        # Consuma e restituisce target seek in sospeso.
        with self._lock:
            target = self._seek_seconds
            self._seek_seconds = None
        return target

    def _is_stop_requested(self) -> bool:
        # Verifica se arresto richiesto.
        with self._lock:
            return bool(self._stop_requested)

    def _is_paused(self) -> bool:
        # Verifica se in pausa.
        with self._lock:
            return bool(self._paused)

    def run(self):
        """Esegue il loop di acquisizione frame."""
        if cv2 is None or self.capture is None:
            return

        while not self._is_stop_requested():
            seek_target = self._consume_seek()
            if seek_target is not None and self.source_kind == "file":
                try:
                    self.capture.set(cv2.CAP_PROP_POS_MSEC, float(seek_target) * 1000.0)
                    self._stream_elapsed_seconds = float(seek_target)
                except Exception:
                    pass

            paused = self._is_paused() if self.source_kind == "file" else False
            force_single_frame = seek_target is not None
            if paused and not force_single_frame:
                time.sleep(min(0.05, self.frame_interval_seconds))
                continue

            decode_started = time.perf_counter()
            ok, frame = self.capture.read()
            decode_ms = (time.perf_counter() - decode_started) * 1000.0

            if not ok or frame is None:
                if self.source_kind == "file":
                    try:
                        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        pass
                    continue

                if not self._warning_emitted:
                    self.capture_warning.emit(
                        f"Stato: connesso ({self.source_kind}) - nessun frame"
                    )
                    self._warning_emitted = True
                time.sleep(min(0.1, self.frame_interval_seconds))
                continue

            self._warning_emitted = False

            if self.source_kind == "file":
                current_seconds = (
                    float(self.capture.get(cv2.CAP_PROP_POS_MSEC) or 0.0) / 1000.0
                )
                if current_seconds <= 0.0:
                    current_seconds = self._stream_elapsed_seconds
                self._stream_elapsed_seconds = float(current_seconds)
            else:
                self._stream_elapsed_seconds += self.frame_interval_seconds
                current_seconds = self._stream_elapsed_seconds

            self.frame_captured.emit(
                frame,
                float(max(0.0, current_seconds)),
                float(max(0.0, decode_ms)),
                self.source_kind,
            )

            if self.source_kind == "file":
                time.sleep(self.frame_interval_seconds)


class RecordingWorker(QThread):
    """Writer asincrono: salva video principale + segmenti crash-safe senza bloccare UI."""

    worker_error = pyqtSignal(str)

    def __init__(
        self,
        output_path: Path,
        crashsafe_segment_dir: Path,
        fps: float,
        frame_size: tuple[int, int],
        *,
        crashsafe_segment_duration_seconds: float = 8.0,
        queue_size: int = 180,
        parent=None,
    ):
        """Inizializza worker registrazione video."""
        super().__init__(parent)
        self.output_path = Path(output_path)
        self.crashsafe_segment_dir = Path(crashsafe_segment_dir)
        self.fps = float(max(1.0, fps))
        self.frame_size = (int(frame_size[0]), int(frame_size[1]))
        self.crashsafe_segment_duration_seconds = float(
            max(1.0, crashsafe_segment_duration_seconds)
        )

        self._queue = Queue(maxsize=max(10, int(queue_size)))
        self._stop_requested = False
        self._dropped_frames = 0

        self._main_writer = self._create_writer(
            self.output_path,
            ["mp4v", "XVID", "MJPG"],
        )

        self._segment_writer = None
        self._segment_index = 0
        self._segment_start_seconds = 0.0

        self.startup_error: str | None = None
        if self._main_writer is None:
            self.startup_error = "Impossibile creare il writer video principale."
        else:
            self.crashsafe_segment_dir.mkdir(parents=True, exist_ok=True)
            if not self._open_new_segment(0.0):
                self.startup_error = (
                    "Impossibile creare il writer crash-safe a segmenti."
                )

    @property
    def dropped_frames(self) -> int:
        """Frame persi per coda piena."""
        return int(self._dropped_frames)

    def is_ready(self) -> bool:
        """Verifica se worker è pronto."""
        return self.startup_error is None and self._main_writer is not None

    def enqueue_frame(self, frame, current_seconds: float) -> bool:
        """Accoda frame per scrittura asincrona."""
        if not self.is_ready():
            return False

        try:
            frame_to_queue = frame.copy()
        except Exception:
            frame_to_queue = frame

        try:
            self._queue.put_nowait((float(current_seconds), frame_to_queue))
            return True
        except Full:
            self._dropped_frames += 1
            return False

    def request_stop(self):
        """Richiede arresto worker."""
        self._stop_requested = True

    def _create_writer(self, path: Path, codec_candidates: list[str]):
        # Crea writer video con codec candidati.
        if cv2 is None:
            return None

        width, height = self.frame_size
        for codec in codec_candidates:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                writer = cv2.VideoWriter(
                    str(path),
                    fourcc,
                    float(self.fps),
                    (int(width), int(height)),
                )
                if writer is not None and writer.isOpened():
                    return writer
                if writer is not None:
                    writer.release()
            except Exception:
                continue
        return None

    def _open_new_segment(self, start_seconds: float) -> bool:
        # Apre nuovo segmento crash-safe.
        if self._segment_writer is not None:
            try:
                self._segment_writer.release()
            except Exception:
                pass
            self._segment_writer = None

        self._segment_index += 1
        self._segment_start_seconds = float(max(0.0, start_seconds))
        segment_path = (
            self.crashsafe_segment_dir / f"segment_{self._segment_index:06d}.avi"
        )
        self._segment_writer = self._create_writer(
            segment_path, ["MJPG", "XVID", "mp4v"]
        )
        return self._segment_writer is not None

    def _rotate_segment_if_needed(self, current_seconds: float):
        # Ruota segmento se durata superata.
        if self._segment_writer is None:
            return

        if float(current_seconds) - float(self._segment_start_seconds) >= float(
            self.crashsafe_segment_duration_seconds
        ):
            self._open_new_segment(current_seconds)

    def run(self):
        """Esegue loop scrittura frame."""
        while True:
            if self._stop_requested and self._queue.empty():
                break

            try:
                current_seconds, frame = self._queue.get(timeout=0.1)
            except Empty:
                continue

            try:
                if self._main_writer is not None:
                    self._main_writer.write(frame)
            except Exception as exc:
                self.worker_error.emit(f"Writer principale errore: {exc}")

            try:
                self._rotate_segment_if_needed(float(current_seconds))
                if self._segment_writer is not None:
                    self._segment_writer.write(frame)
            except Exception as exc:
                self.worker_error.emit(f"Writer crash-safe errore: {exc}")

        if self._main_writer is not None:
            try:
                self._main_writer.release()
            except Exception:
                pass
            self._main_writer = None

        if self._segment_writer is not None:
            try:
                self._segment_writer.release()
            except Exception:
                pass
            self._segment_writer = None


class VideoPlayer(QWidget):
    """Player video con sorgenti file/webcam/IP e preview live."""

    source_changed = pyqtSignal(dict)
    playback_position_changed = pyqtSignal(float)
    playback_state_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        """Inizializza player video."""
        super().__init__(parent)
        self.current_source = None
        self.capture = None
        self.capture_worker: CaptureWorker | None = None
        self.last_frame = None
        self.pending_preview_frame = None
        self.pending_preview_seconds = 0.0
        self.pending_preview_source_kind = ""
        self.pending_preview_dirty = False
        self.frame_interval_seconds = 1.0 / 30.0
        self.stream_elapsed_seconds = 0.0
        self.source_fps = 30.0
        self.source_width = 0
        self.source_height = 0
        self.pending_resume_seconds: float | None = None
        self.file_playback_paused = False

        self.recording_enabled = False
        self.recording_worker: RecordingWorker | None = None
        self.recording_output_path: str | None = None
        self.recording_frame_size: tuple[int, int] | None = None
        self.recording_queue_size = 180
        self.recording_queue_dropped_frames = 0

        self.crashsafe_segment_dir: Path | None = None
        self.crashsafe_segment_duration_seconds = 8.0

        self.preview_delay_seconds = 0.0
        self.delay_buffer = deque()

        # Performance profile (live preview)
        self.performance_profile = "low_latency"
        self.preview_target_fps = 25.0
        self.preview_max_width = 960
        self.live_capture_buffer_size = 1
        self.drop_old_live_frames = True
        self.last_preview_render_ts = 0.0

        # Metriche runtime (finestra mobile di 1s)
        self.metrics_window_start_ts = time.perf_counter()
        self.metrics_input_frames = 0
        self.metrics_rendered_frames = 0
        self.metrics_dropped_frames = 0
        self.metrics_decode_ms_sum = 0.0
        self.metrics_decode_samples = 0
        self.metrics_render_ms_sum = 0.0
        self.metrics_render_samples = 0
        self.metrics_warning_threshold_fps = 18.0
        self.metrics_warning_threshold_drop_pct = 20.0

        # Riconnessione automatica stream IP
        self.ip_reconnect_enabled = True
        self.ip_reconnect_attempt = 0
        self.ip_reconnect_base_delay_seconds = 1.0
        self.ip_reconnect_max_delay_seconds = 10.0
        self.ip_reconnect_reason = ""

        self.render_timer = QTimer(self)
        self.render_timer.setInterval(15)
        self.render_timer.timeout.connect(self._render_pending_frame)

        self.metrics_timer = QTimer(self)
        self.metrics_timer.setInterval(1000)
        self.metrics_timer.timeout.connect(self._refresh_metrics_label)

        self.ip_reconnect_timer = QTimer(self)
        self.ip_reconnect_timer.setSingleShot(True)
        self.ip_reconnect_timer.timeout.connect(self._attempt_ip_reconnect)

        self._setup_ui()
        self._apply_performance_profile(self.performance_profile)
        self._on_source_type_changed()
        self._update_record_button_state()
        self.metrics_timer.start()

    def _setup_ui(self):
        # Costruisce interfaccia utente.
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
        self.source_input.editingFinished.connect(self._on_source_input_edited)
        source_row.addWidget(self.source_input, 1)

        self.webcam_sources = QComboBox()
        self.webcam_sources.setVisible(False)
        self.webcam_sources.currentIndexChanged.connect(self._on_webcam_source_changed)
        source_row.addWidget(self.webcam_sources, 1)

        self.btn_browse = QPushButton("Sfoglia")
        self.btn_browse.clicked.connect(self._browse_file)
        source_row.addWidget(self.btn_browse)

        self.btn_refresh_webcams = QPushButton("Aggiorna webcam")
        self.btn_refresh_webcams.setVisible(False)
        self.btn_refresh_webcams.clicked.connect(self._refresh_webcam_sources)
        source_row.addWidget(self.btn_refresh_webcams)

        layout.addLayout(source_row)

        controls_row = QHBoxLayout()
        self.btn_connect = QPushButton("Connetti")
        self.btn_connect.clicked.connect(
            lambda _checked=False: self._connect_source(show_errors=True)
        )
        controls_row.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Disconnetti")
        self.btn_disconnect.clicked.connect(self._disconnect_source)
        self.btn_disconnect.setEnabled(False)
        controls_row.addWidget(self.btn_disconnect)

        self.btn_pause = QPushButton("Pausa")
        self.btn_pause.clicked.connect(self._toggle_pause_playback)
        self.btn_pause.setEnabled(False)
        controls_row.addWidget(self.btn_pause)

        self.btn_record = QPushButton("Inizia registrazione")
        self.btn_record.clicked.connect(self._toggle_recording)
        self.btn_record.setEnabled(False)
        controls_row.addWidget(self.btn_record)

        controls_row.addWidget(QLabel("Preset:"))

        self.performance_preset = QComboBox()
        self.performance_preset.addItem("Bassa latenza", "low_latency")
        self.performance_preset.addItem("Bilanciato", "balanced")
        self.performance_preset.addItem("Qualità", "quality")
        self.performance_preset.currentIndexChanged.connect(
            self._on_performance_profile_changed
        )
        controls_row.addWidget(self.performance_preset)

        controls_row.addWidget(QLabel("Delay:"))

        self.btn_delay_reset = QPushButton("0")
        self.btn_delay_reset.setToolTip("Azzera il delay preview")
        self.btn_delay_reset.clicked.connect(lambda: self._set_preview_delay(0.0))
        controls_row.addWidget(self.btn_delay_reset)

        self.btn_delay_plus_1 = QPushButton("+1")
        self.btn_delay_plus_1.clicked.connect(lambda: self._change_preview_delay(1.0))
        controls_row.addWidget(self.btn_delay_plus_1)

        self.btn_delay_plus_2 = QPushButton("+2")
        self.btn_delay_plus_2.clicked.connect(lambda: self._change_preview_delay(2.0))
        controls_row.addWidget(self.btn_delay_plus_2)

        self.btn_delay_plus_3 = QPushButton("+3")
        self.btn_delay_plus_3.clicked.connect(lambda: self._change_preview_delay(3.0))
        controls_row.addWidget(self.btn_delay_plus_3)

        self.spin_delay_custom = QSpinBox()
        self.spin_delay_custom.setRange(1, 120)
        self.spin_delay_custom.setValue(5)
        self.spin_delay_custom.setSuffix(" s")
        self.spin_delay_custom.setToolTip("Delay personalizzato (secondi)")
        controls_row.addWidget(self.spin_delay_custom)

        self.btn_delay_plus_n = QPushButton("+n")
        self.btn_delay_plus_n.clicked.connect(
            lambda: self._change_preview_delay(float(self.spin_delay_custom.value()))
        )
        controls_row.addWidget(self.btn_delay_plus_n)

        self.delay_label = QLabel("Delay attivo: 0.0s")
        self.delay_label.setStyleSheet("font-size: 11px;")
        controls_row.addWidget(self.delay_label)

        self.ip_reconnect_label = QLabel("IP reconnect:")
        controls_row.addWidget(self.ip_reconnect_label)

        self.chk_ip_auto_reconnect = QCheckBox("Auto")
        self.chk_ip_auto_reconnect.setChecked(bool(self.ip_reconnect_enabled))
        self.chk_ip_auto_reconnect.stateChanged.connect(self._on_ip_reconnect_toggle)
        controls_row.addWidget(self.chk_ip_auto_reconnect)

        self.spin_ip_reconnect_max = QSpinBox()
        self.spin_ip_reconnect_max.setRange(1, 60)
        self.spin_ip_reconnect_max.setValue(int(self.ip_reconnect_max_delay_seconds))
        self.spin_ip_reconnect_max.setSuffix(" s max")
        self.spin_ip_reconnect_max.setToolTip(
            "Ritardo massimo tra tentativi di reconnessione stream IP"
        )
        self.spin_ip_reconnect_max.valueChanged.connect(
            self._on_ip_reconnect_max_changed
        )
        controls_row.addWidget(self.spin_ip_reconnect_max)

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

        self.metrics_label = QLabel("Metriche: inattivo")
        self.metrics_label.setStyleSheet("font-size: 11px; color: #777;")
        layout.addWidget(self.metrics_label)

    def _on_source_type_changed(self):
        # Gestisce cambio tipo sorgente.
        source_kind = self.source_type.currentData()

        current_kind = str((self.current_source or {}).get("type") or "")
        selected_kind = str(source_kind or "")

        if selected_kind != "ip":
            self._cancel_ip_reconnect(reset_attempts=True)

        if self.capture is not None and current_kind and current_kind != selected_kind:
            self._disconnect_source(silent=True, user_requested=False)

        is_file = source_kind == "file"
        is_webcam = source_kind == "webcam"
        is_ip = source_kind == "ip"

        self.source_input.setVisible(not is_webcam)
        self.webcam_sources.setVisible(is_webcam)
        self.btn_browse.setVisible(is_file)
        self.btn_refresh_webcams.setVisible(is_webcam)

        self.ip_reconnect_label.setVisible(is_ip)
        self.chk_ip_auto_reconnect.setVisible(is_ip)
        self.spin_ip_reconnect_max.setVisible(is_ip)

        # Per i file da filesystem non serve connetti/disconnetti/registrazione manuale
        # In webcam la connessione è automatica, quindi mostriamo Connetti solo per stream IP.
        self.btn_connect.setVisible(source_kind == "ip")
        self.btn_disconnect.setVisible(not is_file)
        self.btn_pause.setVisible(is_file)
        self.btn_record.setVisible(not is_file)

        if is_file:
            self.source_input.setPlaceholderText("Seleziona un file video")
            source_value = self.source_input.text().strip()
            if source_value and Path(source_value).exists():
                self.connect_current_source(force_reconnect=True)
        elif is_webcam:
            self.file_playback_paused = False
            self._refresh_webcam_sources()
        else:
            self.file_playback_paused = False
            self.source_input.setPlaceholderText("URL stream IP (rtsp/http)")

        self._update_pause_button_state()
        self._update_record_button_state()
        self._emit_playback_state()

    def _browse_file(self):
        # Apre dialog selezione file video.
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona video",
            "",
            "Video (*.mp4 *.avi *.mov *.mkv *.m4v);;Tutti i file (*)",
        )
        if file_path:
            self.source_input.setText(file_path)
            self.connect_current_source(force_reconnect=True)

    def _on_source_input_edited(self):
        # Gestisce modifica manuale percorso sorgente.
        source_kind = self.source_type.currentData()
        if source_kind != "file":
            return

        source_value = self.source_input.text().strip()
        if source_value and Path(source_value).exists():
            self.connect_current_source(force_reconnect=True)

    def _scan_webcam_sources(self, max_indices: int = 10) -> list[tuple[str, str]]:
        # Scansiona webcam disponibili.
        if cv2 is None:
            return []

        detected: list[tuple[str, str]] = []
        for index in range(max_indices):
            capture = cv2.VideoCapture(index)
            if capture is None:
                continue

            try:
                if not capture.isOpened():
                    continue

                ok, _ = capture.read()
                if ok:
                    detected.append((f"Webcam {index}", str(index)))
            finally:
                try:
                    capture.release()
                except Exception:
                    pass

        return detected

    def _refresh_webcam_sources(self):
        # Aggiorna lista webcam disponibili.
        previous_value = self.source_input.text().strip()
        devices = self._scan_webcam_sources()

        self.webcam_sources.blockSignals(True)
        self.webcam_sources.clear()

        for label, value in devices:
            self.webcam_sources.addItem(label, value)

        self.webcam_sources.blockSignals(False)

        if not devices:
            self.webcam_sources.addItem("Nessuna webcam rilevata", "")
            self.source_input.clear()
            return

        selected_index = self.webcam_sources.findData(previous_value)
        if selected_index < 0:
            selected_index = 0

        self.webcam_sources.setCurrentIndex(selected_index)
        self._on_webcam_source_changed(selected_index)

    def _on_webcam_source_changed(self, index: int):
        # Gestisce cambio webcam selezionata.
        if index < 0:
            return

        value = str(self.webcam_sources.currentData() or "").strip()
        self.source_input.setText(value)

        # Autoconnessione immediata quando selezioni una webcam valida
        if value:
            self.connect_current_source(force_reconnect=True)

    def _on_performance_profile_changed(self, _index: int | None = None):
# Applica profilo prestazioni selezionato.
        profile = str(self.performance_preset.currentData() or "low_latency")
        self._apply_performance_profile(profile)

        source_kind = str((self.current_source or {}).get("type") or "")
        if (
            self.capture is not None
            and source_kind in {"webcam", "ip"}
            and hasattr(cv2, "CAP_PROP_BUFFERSIZE")
        ):
            try:
                self.capture.set(
                    cv2.CAP_PROP_BUFFERSIZE,
                    int(max(1, self.live_capture_buffer_size)),
                )
            except Exception:
                pass

    def _on_ip_reconnect_toggle(self, _state: int | None = None):
# Attiva/disattiva riconnessione IP.
        self.ip_reconnect_enabled = bool(self.chk_ip_auto_reconnect.isChecked())
        if not self.ip_reconnect_enabled:
            self._cancel_ip_reconnect(reset_attempts=True)

    def _on_ip_reconnect_max_changed(self, value: int):
# Aggiorna ritardo max riconnessione IP.
        self.ip_reconnect_max_delay_seconds = float(max(1, int(value)))

    def _apply_performance_profile(self, profile: str):
# Applica profilo prestazioni video.
        selected = str(profile or "low_latency")
        if selected == "quality":
            self.preview_target_fps = 0.0
            self.preview_max_width = 0
            self.live_capture_buffer_size = 4
            self.drop_old_live_frames = False
        elif selected == "balanced":
            self.preview_target_fps = 30.0
            self.preview_max_width = 1280
            self.live_capture_buffer_size = 2
            self.drop_old_live_frames = True
        else:
            selected = "low_latency"
            self.preview_target_fps = 25.0
            self.preview_max_width = 960
            self.live_capture_buffer_size = 1
            self.drop_old_live_frames = True

        self.performance_profile = selected

    def _cancel_ip_reconnect(self, reset_attempts: bool = True):
# Annulla timer riconnessione IP.
        if hasattr(self, "ip_reconnect_timer") and self.ip_reconnect_timer.isActive():
            self.ip_reconnect_timer.stop()

        if reset_attempts:
            self.ip_reconnect_attempt = 0
            self.ip_reconnect_reason = ""

    def _schedule_ip_reconnect(self, reason: str = ""):
# Pianifica tentativo riconnessione IP.
        if not self.ip_reconnect_enabled:
            return

        if str(self.source_type.currentData() or "") != "ip":
            return

        source_value = self._current_source_value()
        if not source_value:
            return

        if self.ip_reconnect_timer.isActive():
            return

        self.ip_reconnect_attempt += 1
        self.ip_reconnect_reason = str(reason or "").strip()

        attempt_idx = max(1, int(self.ip_reconnect_attempt))
        delay_seconds = min(
            float(self.ip_reconnect_max_delay_seconds),
            float(self.ip_reconnect_base_delay_seconds) * (2 ** (attempt_idx - 1)),
        )
        reason_suffix = (
            f" • {self.ip_reconnect_reason}" if self.ip_reconnect_reason else ""
        )
        self.status_label.setText(
            f"Stato: stream IP instabile, riconnessione in {delay_seconds:.1f}s "
            f"(tentativo {attempt_idx}){reason_suffix}"
        )
        self.ip_reconnect_timer.start(max(1, int(delay_seconds * 1000.0)))

    def _attempt_ip_reconnect(self):
# Tenta riconnessione stream IP.
        if not self.ip_reconnect_enabled:
            return

        if str(self.source_type.currentData() or "") != "ip":
            self._cancel_ip_reconnect(reset_attempts=True)
            return

        source_value = self._current_source_value()
        if not source_value:
            self._cancel_ip_reconnect(reset_attempts=True)
            return

        worker_running = bool(
            self.capture is not None
            and self.capture_worker is not None
            and self.capture_worker.isRunning()
        )
        if worker_running:
            self._cancel_ip_reconnect(reset_attempts=True)
            return

        attempt_idx = max(1, int(self.ip_reconnect_attempt))
        self.status_label.setText(
            f"Stato: riconnessione stream IP in corso (tentativo {attempt_idx})"
        )

        connected = self.connect_current_source(
            force_reconnect=True,
            show_errors=False,
        )
        if connected:
            self.status_label.setText("Stato: connesso (ip) • riconnesso")
            self._cancel_ip_reconnect(reset_attempts=True)
        else:
            self._schedule_ip_reconnect("retry")

    def _reset_runtime_metrics(self):
# Azzera metriche runtime.
        self.metrics_window_start_ts = time.perf_counter()
        self.metrics_input_frames = 0
        self.metrics_rendered_frames = 0
        self.metrics_dropped_frames = 0
        self.metrics_decode_ms_sum = 0.0
        self.metrics_decode_samples = 0
        self.metrics_render_ms_sum = 0.0
        self.metrics_render_samples = 0

    def _track_runtime_metrics(
        self,
        *,
        input_frames: int = 0,
        rendered_frames: int = 0,
        dropped_frames: int = 0,
        decode_ms: float | None = None,
        render_ms: float | None = None,
    ):
        # Aggiorna metriche runtime con nuovi dati.
        self.metrics_input_frames += max(0, int(input_frames))
        self.metrics_rendered_frames += max(0, int(rendered_frames))
        self.metrics_dropped_frames += max(0, int(dropped_frames))

        if decode_ms is not None:
            self.metrics_decode_ms_sum += max(0.0, float(decode_ms))
            self.metrics_decode_samples += 1

        if render_ms is not None:
            self.metrics_render_ms_sum += max(0.0, float(render_ms))
            self.metrics_render_samples += 1

    def _refresh_metrics_label(self):
# Aggiorna etichetta metriche a schermo.
        if not hasattr(self, "metrics_label"):
            return

        if self.capture is None:
            self.metrics_label.setText("Metriche: inattivo")
            self.metrics_label.setStyleSheet("font-size: 11px; color: #777;")
            self._reset_runtime_metrics()
            return

        worker = self.recording_worker
        if worker is not None:
            self.recording_queue_dropped_frames = int(worker.dropped_frames)

        elapsed = max(0.001, time.perf_counter() - self.metrics_window_start_ts)
        input_fps = self.metrics_input_frames / elapsed
        render_fps = self.metrics_rendered_frames / elapsed
        drop_pct = (
            (self.metrics_dropped_frames / self.metrics_input_frames) * 100.0
            if self.metrics_input_frames > 0
            else 0.0
        )

        decode_ms_avg = (
            self.metrics_decode_ms_sum / self.metrics_decode_samples
            if self.metrics_decode_samples > 0
            else 0.0
        )
        render_ms_avg = (
            self.metrics_render_ms_sum / self.metrics_render_samples
            if self.metrics_render_samples > 0
            else 0.0
        )

        enough_samples = self.metrics_input_frames >= 10
        warn = enough_samples and (
            render_fps < self.metrics_warning_threshold_fps
            or drop_pct > self.metrics_warning_threshold_drop_pct
        )
        prefix = "⚠ " if warn else ""

        self.metrics_label.setText(
            f"{prefix}Metriche [{self.performance_profile}]: "
            f"in {input_fps:.1f} fps | out {render_fps:.1f} fps | "
            f"decode {decode_ms_avg:.1f} ms | render {render_ms_avg:.1f} ms | "
            f"drop {drop_pct:.1f}% | rec_q_drop {self.recording_queue_dropped_frames}"
        )
        self.metrics_label.setStyleSheet(
            "font-size: 11px; color: #C0392B;"
            if warn
            else "font-size: 11px; color: #2D6A4F;"
        )

        self._reset_runtime_metrics()

    def _resize_preview_frame_if_needed(self, source_kind: str | None, frame):
# Ridimensiona frame anteprima se necessario.
        kind = str(source_kind or "")
        max_width = int(self.preview_max_width or 0)
        if kind not in {"webcam", "ip"} or max_width <= 0:
            return frame

        try:
            height, width = frame.shape[:2]
        except Exception:
            return frame

        if width <= max_width:
            return frame

        target_width = max_width
        target_height = max(1, int((height * target_width) / width))
        try:
            return cv2.resize(frame, (target_width, target_height))
        except Exception:
            return frame

    def _build_capture_source(self, source_kind: str, source_value: str):
# Costruisce sorgente per cv2.VideoCapture.
        if source_kind == "webcam":
            try:
                return int(source_value)
            except ValueError:
                return source_value
        return source_value

    def _set_preview_delay(self, seconds: float):
# Imposta delay anteprima in secondi.
        try:
            value = max(0.0, min(120.0, float(seconds)))
        except Exception:
            value = 0.0

        self.preview_delay_seconds = value
        self.delay_buffer.clear()
        self._refresh_delay_label()

    def _change_preview_delay(self, delta_seconds: float):
# Modifica delay anteprima di un delta.
        try:
            delta = float(delta_seconds)
        except Exception:
            delta = 0.0
        self._set_preview_delay(self.preview_delay_seconds + delta)

    def _refresh_delay_label(self):
# Aggiorna etichetta delay.
        if hasattr(self, "delay_label"):
            self.delay_label.setText(f"Delay attivo: {self.preview_delay_seconds:.1f}s")

    def _recordings_dir(self) -> Path:
# Directory registrazioni in home.
        target = Path.home() / "VolleyballScoutRecordings"
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _can_record_live_source(self) -> bool:
# Verifica se registrazione live possibile.
        source_kind = (self.current_source or {}).get("type")
        return bool(
            cv2 is not None
            and self.capture is not None
            and source_kind in {"webcam", "ip"}
        )

    def _is_file_source_connected(self) -> bool:
# Verifica se sorgente file connessa.
        source_kind = str((self.current_source or {}).get("type") or "")
        return bool(
            source_kind == "file"
            and self.capture is not None
            and self.capture_worker is not None
        )

    def _update_pause_button_state(self):
# Aggiorna stato pulsante pausa.
        if not hasattr(self, "btn_pause"):
            return

        is_file_connected = self._is_file_source_connected()
        self.btn_pause.setEnabled(is_file_connected)
        self.btn_pause.setText(
            "Riprendi" if self.file_playback_paused and is_file_connected else "Pausa"
        )

    def _set_pause_state(self, paused: bool, emit_state: bool = True):
# Imposta stato pausa e notifica worker.
        next_paused = bool(paused)
        self.file_playback_paused = (
            next_paused if self._is_file_source_connected() else False
        )

        worker = self.capture_worker
        if worker is not None:
            try:
                worker.request_pause(self.file_playback_paused)
            except Exception:
                pass

        source_kind = str((self.current_source or {}).get("type") or "")
        if source_kind == "file" and self.capture is not None:
            if self.file_playback_paused:
                self.status_label.setText("Stato: connesso (file) • in pausa")
            else:
                self.status_label.setText("Stato: connesso (file)")

        self._update_pause_button_state()
        if emit_state:
            self._emit_playback_state()

    def set_paused(self, paused: bool):
        """API pubblica: pausa/riprende la riproduzione file locale."""
        if not self._is_file_source_connected():
            return
        self._set_pause_state(bool(paused), emit_state=True)

    def toggle_pause(self):
        """API pubblica: toggle pausa/ripresa per sorgente file."""
        if not self._is_file_source_connected():
            return
        self._set_pause_state(not self.file_playback_paused, emit_state=True)

    def _toggle_pause_playback(self):
# Toggle pausa riproduzione.
        self.toggle_pause()

    def _update_record_button_state(self):
# Aggiorna stato pulsante registrazione.
        if not hasattr(self, "btn_record"):
            return

        can_record = self._can_record_live_source()
        self.btn_record.setEnabled(can_record or self.recording_enabled)
        self.btn_record.setText(
            "Stop registrazione" if self.recording_enabled else "Inizia registrazione"
        )

    def _emit_playback_state(self):
# Emette stato riproduzione corrente.
        source_kind = str((self.current_source or {}).get("type") or "")
        payload = {
            "connected": bool(self.capture is not None),
            "type": source_kind or None,
            "is_live": source_kind in {"webcam", "ip"},
            "paused": bool(source_kind == "file" and self.file_playback_paused),
            "seconds": float(max(0.0, self.stream_elapsed_seconds)),
        }
        self.playback_state_changed.emit(payload)

    def _emit_source_changed(self):
# Emette evento cambio sorgente.
        payload = dict(self.current_source or {})
        if self.recording_output_path:
            payload["recorded_path"] = self.recording_output_path
        if self.crashsafe_segment_dir is not None:
            payload["recorded_backup_dir"] = str(self.crashsafe_segment_dir)
        payload["recording"] = bool(self.recording_enabled)
        self.source_changed.emit(payload)
        self._emit_playback_state()

    def _compute_recording_queue_size(self, fps: float) -> int:
# Calcola dimensione coda registrazione.
        safe_fps = max(1.0, float(fps))
        if self.performance_profile == "quality":
            window_seconds = 6.0
        elif self.performance_profile == "balanced":
            window_seconds = 4.0
        else:
            window_seconds = 3.0
        return int(max(60, min(900, safe_fps * window_seconds)))

    def _toggle_recording(self):
# Avvia/ferma registrazione.
        if self.recording_enabled:
            self._stop_recording(silent=False)
        else:
            self._start_recording()

    def _start_recording(self):
# Avvia registrazione video.
        if cv2 is None:
            return
        if not self._can_record_live_source():
            QMessageBox.information(
                self,
                "Registrazione non disponibile",
                "La registrazione è disponibile solo per webcam locale o stream IP connessi.",
            )
            return

        width = int(self.source_width or 0)
        height = int(self.source_height or 0)
        if (width <= 0 or height <= 0) and self.capture is not None:
            try:
                width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            except Exception:
                width, height = 0, 0
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

        fps = float(self.source_fps or 0.0)
        if (fps <= 1.0 or fps > 120.0) and self.capture is not None:
            try:
                fps = float(self.capture.get(cv2.CAP_PROP_FPS) or 0.0)
            except Exception:
                fps = 0.0
        if fps <= 1.0 or fps > 120.0:
            fps = 30.0

        source_kind = str((self.current_source or {}).get("type") or "live")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self._recordings_dir() / f"scout_{source_kind}_{stamp}.mp4"

        self.crashsafe_segment_dir = (
            self._recordings_dir() / f"scout_{source_kind}_{stamp}_segments"
        )

        queue_size = self._compute_recording_queue_size(fps)
        worker = RecordingWorker(
            output_path=output_path,
            crashsafe_segment_dir=self.crashsafe_segment_dir,
            fps=fps,
            frame_size=(int(width), int(height)),
            crashsafe_segment_duration_seconds=self.crashsafe_segment_duration_seconds,
            queue_size=queue_size,
            parent=self,
        )
        if not worker.is_ready():
            QMessageBox.warning(
                self,
                "Errore registrazione",
                worker.startup_error
                or "Impossibile iniziare la registrazione locale del video.",
            )
            self.crashsafe_segment_dir = None
            return

        worker.worker_error.connect(self._on_recording_worker_error)
        worker.start()

        self.recording_worker = worker
        self.recording_frame_size = (int(width), int(height))
        self.recording_output_path = str(output_path)
        self.recording_enabled = True
        self.recording_queue_size = int(queue_size)
        self.recording_queue_dropped_frames = 0

        # Sincronizza il tempo scouting al nuovo video registrato (t=0)
        self.stream_elapsed_seconds = 0.0
        self.pending_resume_seconds = 0.0
        self.delay_buffer.clear()
        self.playback_position_changed.emit(0.0)

        source_kind_text = str((self.current_source or {}).get("type") or "live")
        self.status_label.setText(f"Stato: connesso ({source_kind_text}) • REC async")
        self._update_record_button_state()
        self._emit_source_changed()

    def _on_recording_worker_error(self, message: str):
# Gestisce errore worker registrazione.
        source_kind = str((self.current_source or {}).get("type") or "live")
        self.status_label.setText(f"Stato: connesso ({source_kind}) • REC warning")
        if message:
            self.status_label.setToolTip(message)

    def _enqueue_record_frame(self, frame, current_seconds: float):
# Accoda frame al worker registrazione.
        worker = self.recording_worker
        if not self.recording_enabled or worker is None:
            return

        frame_to_save = frame
        if self.recording_frame_size is not None:
            rec_w, rec_h = self.recording_frame_size
            if frame.shape[1] != rec_w or frame.shape[0] != rec_h:
                try:
                    frame_to_save = cv2.resize(frame, (rec_w, rec_h))
                except Exception:
                    frame_to_save = frame

        worker.enqueue_frame(frame_to_save, float(current_seconds))

    def _stop_recording(self, silent: bool = False):
# Ferma registrazione video.
        was_recording = self.recording_enabled
        worker = self.recording_worker

        if worker is not None:
            worker.request_stop()
            if not worker.wait(5000):
                worker.terminate()
                worker.wait(500)
            self.recording_queue_dropped_frames = max(
                self.recording_queue_dropped_frames,
                int(worker.dropped_frames),
            )

        self.recording_worker = None
        self.recording_frame_size = None
        self.recording_enabled = False

        source_kind = str((self.current_source or {}).get("type") or "")
        if self.capture is not None:
            if self.recording_output_path and was_recording:
                drop_note = (
                    f" • drop coda={self.recording_queue_dropped_frames}"
                    if self.recording_queue_dropped_frames > 0
                    else ""
                )
                self.status_label.setText(
                    f"Stato: connesso ({source_kind}) • registrazione salvata{drop_note}"
                )
            else:
                self.status_label.setText(f"Stato: connesso ({source_kind})")

        self._update_record_button_state()
        if was_recording and not silent:
            self._emit_source_changed()

    def connect_current_source(
        self,
        force_reconnect: bool = False,
        show_errors: bool = True,
    ) -> bool:
        """Connette la sorgente attualmente impostata nei controlli."""
        source_kind = self.source_type.currentData()
        source_value = self._current_source_value()

        if not force_reconnect and self.capture is not None and self.current_source:
            same_source = (
                str(self.current_source.get("type") or "") == str(source_kind or "")
                and str(self.current_source.get("value") or "") == source_value
            )
            worker_running = bool(
                self.capture_worker is not None and self.capture_worker.isRunning()
            )
            if same_source and worker_running:
                return True

        self._connect_source(show_errors=show_errors)
        return bool(self.capture is not None and self.capture_worker is not None)

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
            self.stream_elapsed_seconds = target
            self.delay_buffer.clear()
            worker = self.capture_worker
            if worker is not None:
                worker.request_seek(target)
            self._emit_playback_state()

    def seek_to(self, seconds: float | None):
        """API pubblica: seek del video (alias di set_resume_position)."""
        self.set_resume_position(seconds)

    def _current_source_value(self) -> str:
# Valore sorgente corrente dai controlli.
        source_kind = self.source_type.currentData()
        if source_kind == "webcam":
            webcam_value = str(self.webcam_sources.currentData() or "").strip()
            if webcam_value:
                return webcam_value
        return self.source_input.text().strip()

    def _connect_source(self, show_errors: bool = True):
# Connette effettivamente la sorgente video.
        if cv2 is None:
            if show_errors:
                QMessageBox.critical(
                    self,
                    "OpenCV non disponibile",
                    "Modulo cv2 non trovato. Installa opencv-python nell'ambiente corrente.",
                )
            else:
                self.status_label.setText("Stato: OpenCV non disponibile")
            return

        source_kind = self.source_type.currentData()
        source_value = self._current_source_value()

        if not source_value:
            if show_errors:
                QMessageBox.warning(
                    self, "Sorgente mancante", "Inserisci una sorgente video valida."
                )
            else:
                self.status_label.setText("Stato: sorgente video mancante")
            return

        if source_kind == "file":
            path = Path(source_value)
            if not path.exists():
                if show_errors:
                    QMessageBox.warning(
                        self,
                        "File non trovato",
                        f"Il file selezionato non esiste:\n{source_value}",
                    )
                else:
                    self.status_label.setText("Stato: file video non trovato")
                return

        self._disconnect_source(silent=True, user_requested=False)

        self.recording_output_path = None
        self.crashsafe_segment_dir = None
        self.recording_queue_dropped_frames = 0

        cap_source = self._build_capture_source(source_kind, source_value)
        capture = cv2.VideoCapture(cap_source)

        if (
            capture is not None
            and source_kind in {"webcam", "ip"}
            and hasattr(cv2, "CAP_PROP_BUFFERSIZE")
        ):
            try:
                capture.set(
                    cv2.CAP_PROP_BUFFERSIZE, int(max(1, self.live_capture_buffer_size))
                )
            except Exception:
                pass

        if capture is None or not capture.isOpened():
            if capture is not None:
                capture.release()
            if show_errors:
                QMessageBox.warning(
                    self,
                    "Connessione fallita",
                    "Impossibile aprire la sorgente video selezionata.",
                )
            else:
                self.status_label.setText("Stato: connessione sorgente fallita")
            return

        self.capture = capture
        self.current_source = {"type": source_kind, "value": source_value}
        self.last_preview_render_ts = 0.0
        self.pending_preview_frame = None
        self.pending_preview_seconds = 0.0
        self.pending_preview_source_kind = str(source_kind or "")
        self.pending_preview_dirty = False
        self._reset_runtime_metrics()

        try:
            self.source_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            self.source_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        except Exception:
            self.source_width = 0
            self.source_height = 0

        fps = float(self.capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 1.0 or fps > 120.0:
            fps = 30.0
        self.source_fps = float(fps)
        interval_ms = max(15, int(1000.0 / fps))
        self.frame_interval_seconds = interval_ms / 1000.0
        self.stream_elapsed_seconds = 0.0

        self._stop_capture_worker()
        worker = CaptureWorker(
            self.capture,
            str(source_kind or ""),
            self.frame_interval_seconds,
            parent=self,
        )
        worker.frame_captured.connect(self._on_capture_frame)
        worker.capture_warning.connect(self._on_capture_warning)
        self.capture_worker = worker

        if source_kind == "file" and self.pending_resume_seconds is not None:
            try:
                target = max(0.0, float(self.pending_resume_seconds))
                self.stream_elapsed_seconds = target
                worker.request_seek(target)
            except Exception:
                pass

        self.delay_buffer.clear()
        self.render_timer.start()
        worker.start()

        self.file_playback_paused = False
        self._set_pause_state(False, emit_state=False)

        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(True)
        self.status_label.setText(f"Stato: connesso ({source_kind})")

        self._cancel_ip_reconnect(reset_attempts=True)

        self._update_pause_button_state()
        self._update_record_button_state()
        self._emit_source_changed()

    def _select_preview_frame(
        self,
        source_kind: str | None,
        frame,
        current_seconds: float,
    ):
        # Seleziona frame con delay per anteprima.
        kind = str(source_kind or "")
        if kind not in {"webcam", "ip"} or self.preview_delay_seconds <= 0.0:
            self.delay_buffer.clear()
            return frame, max(0.0, float(current_seconds))

        try:
            self.delay_buffer.append((float(current_seconds), frame.copy()))
        except Exception:
            self.delay_buffer.append((float(current_seconds), frame))

        target_seconds = float(current_seconds) - float(self.preview_delay_seconds)

        # Mantieni solo buffer utile (delay + margine)
        keep_from = target_seconds - 2.0
        while len(self.delay_buffer) > 2 and self.delay_buffer[0][0] < keep_from:
            self.delay_buffer.popleft()

        if target_seconds <= 0.0:
            ts, frm = self.delay_buffer[0]
            return frm, max(0.0, float(ts))

        while len(self.delay_buffer) >= 2 and self.delay_buffer[1][0] <= target_seconds:
            self.delay_buffer.popleft()

        ts, frm = self.delay_buffer[0]
        return frm, max(0.0, float(ts))

    def _stop_capture_worker(self):
# Ferma worker acquisizione frame.
        worker = self.capture_worker
        if worker is None:
            return

        worker.request_stop()
        if not worker.wait(3000):
            worker.terminate()
            worker.wait(300)
        self.capture_worker = None

    def _on_capture_warning(self, status_text: str):
# Gestisce warning dal worker.
        if self.capture is None:
            return

        source_kind = str(
            (self.current_source or {}).get("type")
            or self.source_type.currentData()
            or ""
        )
        if source_kind == "ip":
            self._schedule_ip_reconnect("nessun frame")
            return

        self.status_label.setText(str(status_text or "Stato: connesso - warning"))

    def _on_capture_frame(
        self,
        frame,
        current_seconds: float,
        decode_ms: float,
        source_kind: str,
    ):
        # Gestisce frame catturato dal worker.
        if self.capture is None:
            return

        self.stream_elapsed_seconds = max(0.0, float(current_seconds))

        if str(source_kind or "") == "ip":
            self._cancel_ip_reconnect(reset_attempts=True)

        if self.recording_enabled:
            self._enqueue_record_frame(frame, self.stream_elapsed_seconds)

        preview_frame, preview_seconds = self._select_preview_frame(
            str(source_kind or ""), frame, self.stream_elapsed_seconds
        )
        preview_frame = self._resize_preview_frame_if_needed(
            str(source_kind or ""), preview_frame
        )

        self.pending_preview_frame = preview_frame
        self.pending_preview_seconds = max(0.0, float(preview_seconds))
        self.pending_preview_source_kind = str(source_kind or "")
        self.pending_preview_dirty = True

        self.playback_position_changed.emit(max(0.0, float(preview_seconds)))
        self._track_runtime_metrics(input_frames=1, decode_ms=decode_ms)

    def _render_pending_frame(self):
# Renderizza frame in attesa.
        if self.capture is None or not self.pending_preview_dirty:
            return

        preview_frame = self.pending_preview_frame
        kind = str(self.pending_preview_source_kind or "")

        is_live = kind in {"webcam", "ip"}
        should_render = True

        now_ts = time.perf_counter()
        if is_live and self.preview_target_fps > 0.0:
            min_interval = 1.0 / max(1.0, float(self.preview_target_fps))
            if (
                self.last_preview_render_ts > 0.0
                and (now_ts - self.last_preview_render_ts) < min_interval
            ):
                should_render = False

        if not should_render:
            self._track_runtime_metrics(
                dropped_frames=1 if is_live else 0,
            )
            return

        render_started = time.perf_counter()
        self.last_frame = preview_frame
        self._render_frame(preview_frame)
        render_ms = (time.perf_counter() - render_started) * 1000.0
        self.last_preview_render_ts = now_ts
        self.pending_preview_dirty = False

        self._track_runtime_metrics(rendered_frames=1, render_ms=render_ms)

    def _render_frame(self, frame):
# Converte e mostra frame nell'anteprima.
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

    def _disconnect_source(self, silent: bool = False, user_requested: bool = True):
# Disconnette sorgente video.
        if user_requested:
            self._cancel_ip_reconnect(reset_attempts=True)

        self.render_timer.stop()
        self._stop_capture_worker()

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
        self.pending_preview_frame = None
        self.pending_preview_seconds = 0.0
        self.pending_preview_source_kind = ""
        self.pending_preview_dirty = False
        self.stream_elapsed_seconds = 0.0
        self.file_playback_paused = False
        self.source_fps = 30.0
        self.source_width = 0
        self.source_height = 0
        self.delay_buffer.clear()
        self.last_preview_render_ts = 0.0
        self._reset_runtime_metrics()

        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self._update_pause_button_state()
        self._update_record_button_state()
        self.status_label.setText("Stato: inattivo")
        self.preview_label.clear()
        self.preview_label.setText("Anteprima video non ancora disponibile")
        if hasattr(self, "metrics_label"):
            self.metrics_label.setText("Metriche: inattivo")
            self.metrics_label.setStyleSheet("font-size: 11px; color: #777;")

        if not silent:
            payload = {"type": None, "value": None, "recording": False}
            if self.recording_output_path:
                payload["recorded_path"] = self.recording_output_path
            if self.crashsafe_segment_dir is not None:
                payload["recorded_backup_dir"] = str(self.crashsafe_segment_dir)
            self.source_changed.emit(payload)
            self.playback_position_changed.emit(0.0)

        self._emit_playback_state()

    def resizeEvent(self, event):
        """Ridimensiona anteprima con la finestra."""
        super().resizeEvent(event)
        if self.last_frame is not None:
            self._render_frame(self.last_frame)

    def closeEvent(self, event):
        """Pulisce risorse alla chiusura."""
        self.metrics_timer.stop()
        self._cancel_ip_reconnect(reset_attempts=True)
        self._disconnect_source(silent=True, user_requested=False)
        super().closeEvent(event)
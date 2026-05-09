from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

try:
    from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
    from PyQt6.QtGui import (
        QAction,
        QColor,
        QImage,
        QMouseEvent,
        QPainter,
        QPen,
        QPixmap,
    )
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QGridLayout,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyQt6 non installato. Esegui: pip install PyQt6") from exc

import os
import shutil
import subprocess
import time

from ..core.config import AppConfig
from ..pipeline.analysis_pipeline import PipelineConfig, VolleyballAnalysisPipeline


class CommandWorker(QThread):
    log_message = pyqtSignal(str)
    finished_success = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(self, command: list[str], cwd: str | None = None) -> None:
        super().__init__()
        self.command = command
        self.cwd = cwd

    def run(self) -> None:
        try:
            self.log_message.emit("Eseguo: " + " ".join(self.command))
            process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert process.stdout is not None
            for line in process.stdout:
                self.log_message.emit(line.rstrip())
            return_code = process.wait()
            if return_code == 0:
                self.finished_success.emit("Comando completato")
            else:
                self.finished_error.emit(f"Comando terminato con codice {return_code}")
        except Exception:
            import traceback

            self.finished_error.emit(traceback.format_exc())


class AnalysisWorker(QThread):
    log_message = pyqtSignal(str)
    progress_update = pyqtSignal(dict)
    finished_success = pyqtSignal(dict)
    finished_error = pyqtSignal(str)

    def __init__(self, config: PipelineConfig, chunk_seconds=60) -> None:
        super().__init__()
        self.config = config
        self.chunk_seconds = chunk_seconds
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self) -> None:
        try:
            self.log_message.emit("Avvio pipeline di analisi...")
            pipeline = VolleyballAnalysisPipeline(self.config)
            self.log_message.emit(
                f"Video caricato: {pipeline.video.source.source_path}"
            )
            self.log_message.emit(
                f"Metadata: {pipeline.video.metadata.width}x{pipeline.video.metadata.height}, "
                f"fps={pipeline.video.metadata.fps:.2f}, durata={pipeline.video.metadata.duration_seconds:.1f}s"
            )
            exported = pipeline.run_chunked(
                chunk_seconds=self.chunk_seconds,
                progress_callback=self._emit_progress,
                stop_callback=lambda: self._stop_requested,
            )
            if self._stop_requested:
                self.log_message.emit("Analisi interrotta dall'utente")
                self.finished_error.emit("Analisi interrotta dall'utente")
                return
            self.log_message.emit("Analisi completata con successo")
            self.finished_success.emit(
                {key: str(value.resolve()) for key, value in exported.items()}
            )
        except Exception as exc:  # pragma: no cover
            import traceback

            tb = traceback.format_exc()
            self.finished_error.emit(tb)

    def _emit_progress(self, payload: dict) -> None:
        self.progress_update.emit(payload)


class ClickableImageLabel(QLabel):
    point_added = pyqtSignal(float, float)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(480, 270)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pixmap_image: QPixmap | None = None
        self.points: list[tuple[float, float]] = []

    def set_image(self, pixmap: QPixmap) -> None:
        self.pixmap_image = pixmap
        self._refresh()

    def set_points(self, points: list[list[float]] | list[tuple[float, float]]) -> None:
        self.points = [(float(x), float(y)) for x, y in points]
        self._refresh()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # pragma: no cover
        if self.pixmap_image is None:
            return

        scaled = self.pixmap_image.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        offset_x = (self.width() - scaled.width()) / 2
        offset_y = (self.height() - scaled.height()) / 2
        click_x = event.position().x() - offset_x
        click_y = event.position().y() - offset_y

        if (
            click_x < 0
            or click_y < 0
            or click_x > scaled.width()
            or click_y > scaled.height()
        ):
            return

        image_x = click_x * self.pixmap_image.width() / scaled.width()
        image_y = click_y * self.pixmap_image.height() / scaled.height()
        self.point_added.emit(float(image_x), float(image_y))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        if self.pixmap_image is None:
            return
        pixmap = self._draw_overlay()
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)

    def _draw_overlay(self) -> QPixmap:
        assert self.pixmap_image is not None
        pixmap = self.pixmap_image.copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        point_pen = QPen(QColor(255, 0, 0))
        point_pen.setWidth(10)
        painter.setPen(point_pen)
        for index, (x, y) in enumerate(self.points, start=1):
            painter.drawPoint(int(x), int(y))
            painter.drawText(int(x) + 12, int(y) - 12, str(index))

        if len(self.points) == 4:
            polygon_pen = QPen(QColor(255, 215, 0))
            polygon_pen.setWidth(3)
            painter.setPen(polygon_pen)
            for idx in range(4):
                x1, y1 = self.points[idx]
                x2, y2 = self.points[(idx + 1) % 4]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            zone_pen = QPen(QColor(0, 255, 0, 180))
            zone_pen.setWidth(2)
            painter.setPen(zone_pen)
            for line in build_court_overlay_lines(self.points):
                painter.drawLine(int(line[0]), int(line[1]), int(line[2]), int(line[3]))

        painter.end()
        return pixmap


def build_court_overlay_lines(
    points: list[tuple[float, float]],
) -> list[tuple[float, float, float, float]]:
    src = np.float32(points)
    dst = np.float32([[0, 0], [900, 0], [900, 1800], [0, 1800]])
    homography = cv2.getPerspectiveTransform(dst, src)
    lines: list[tuple[float, float, float, float]] = []

    for x in [300, 600]:
        p1 = cv2.perspectiveTransform(
            np.array([[[x, 0]]], dtype=np.float32), homography
        )[0][0]
        p2 = cv2.perspectiveTransform(
            np.array([[[x, 1800]]], dtype=np.float32), homography
        )[0][0]
        lines.append((float(p1[0]), float(p1[1]), float(p2[0]), float(p2[1])))

    for y in [450, 900, 1350]:
        p1 = cv2.perspectiveTransform(
            np.array([[[0, y]]], dtype=np.float32), homography
        )[0][0]
        p2 = cv2.perspectiveTransform(
            np.array([[[900, y]]], dtype=np.float32), homography
        )[0][0]
        lines.append((float(p1[0]), float(p1[1]), float(p2[0]), float(p2[1])))

    return lines


class CalibrationDialog(QDialog):
    def __init__(self, frame_bgr: np.ndarray, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Calibrazione campo")
        self.resize(1280, 820)
        self.points: list[list[float]] = []
        self.frame_bgr = frame_bgr
        self.config = AppConfig()
        self.num_fields = 1  # Default: 1 campo
        self._build_ui()
        self._set_main_image()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Opzione numero di campi
        fields_layout = QHBoxLayout()
        fields_label = QLabel("Numero di campi nel video:")
        fields_layout.addWidget(fields_label)

        self.fields_combo = QComboBox()
        self.fields_combo.addItems(["1 campo", "2 campi (uno sopra, uno sotto)"])
        self.fields_combo.currentIndexChanged.connect(self._on_fields_changed)
        fields_layout.addWidget(self.fields_combo)
        fields_layout.addStretch()
        layout.addLayout(fields_layout)

        self.info = QLabel(
            "Clicca i 4 angoli del campo in ordine: alto-sinistra, alto-destra, basso-destra, basso-sinistra"
        )
        layout.addWidget(self.info)

        grid = QGridLayout()
        layout.addLayout(grid, 1)

        self.image_label = ClickableImageLabel()
        self.image_label.point_added.connect(self._add_point)
        grid.addWidget(QLabel("Frame originale + overlay"), 0, 0)
        grid.addWidget(self.image_label, 1, 0)

        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(480, 270)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel("Preview top-down"), 0, 1)
        grid.addWidget(self.preview_label, 1, 1)

        controls = QHBoxLayout()
        reset_btn = QPushButton("Reset punti")
        reset_btn.clicked.connect(self._reset_points)
        load_btn = QPushButton("Carica salvati")
        load_btn.clicked.connect(self._load_saved_points)
        save_btn = QPushButton("Salva calibrazione")
        save_btn.clicked.connect(self._save_points)
        controls.addWidget(reset_btn)
        controls.addWidget(load_btn)
        controls.addWidget(save_btn)
        layout.addLayout(controls)

    def _on_fields_changed(self, index: int):
        """Cambia il numero di campi."""
        self.num_fields = 1 if index == 0 else 2
        self.info.setText(
            f"[{self.num_fields} campo/i] Clicca i 4 angoli: alto-sinistra, alto-destra, basso-destra, basso-sinistra"
        )

        self._set_main_image()
        self._update_topdown_preview()

    def _set_main_image(self) -> None:
        rgb = cv2.cvtColor(self.frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.image_label.set_image(QPixmap.fromImage(image.copy()))
        self.image_label.set_points(self.points)
        self._update_topdown_preview()

    def _add_point(self, x: float, y: float) -> None:
        if len(self.points) >= 4:
            return
        self.points.append([round(x, 2), round(y, 2)])
        self.image_label.set_points(self.points)
        self.info.setText(f"Punti selezionati: {len(self.points)}/4")
        self._update_topdown_preview()

    def _reset_points(self) -> None:
        self.points = []
        self.image_label.set_points(self.points)
        self.info.setText(
            "Clicca i 4 angoli del campo in ordine: alto-sinistra, alto-destra, basso-destra, basso-sinistra"
        )
        self._update_topdown_preview()

    def _load_saved_points(self) -> None:
        self.points = self.config.load_field_points()
        self.image_label.set_points(self.points)
        self.info.setText("Punti caricati da configurazione salvata")
        self._update_topdown_preview()

    def _save_points(self) -> None:
        if len(self.points) != 4:
            QMessageBox.warning(self, "Errore", "Devi selezionare esattamente 4 punti")
            return
        saved_path = self.config.save_field_points(self.points, self.num_fields)
        QMessageBox.information(
            self,
            "Salvato",
            f"Calibrazione salvata in: {saved_path}\nCampi: {self.num_fields}",
        )
        self.accept()

    def _update_topdown_preview(self) -> None:
        preview = self._build_topdown_preview()
        rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image.copy())
        self.preview_label.setPixmap(
            pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_topdown_preview()

    def _build_topdown_preview(self):
        canvas = np.full((900, 500, 3), 35, dtype=np.uint8)
        cv2.rectangle(canvas, (50, 50), (450, 850), (255, 255, 255), 3)
        for x in [183, 316]:
            cv2.line(canvas, (x, 50), (x, 850), (80, 200, 80), 2)
        for y in [250, 450, 650]:
            color = (0, 0, 255) if y == 450 else (80, 200, 80)
            thickness = 4 if y == 450 else 2
            cv2.line(canvas, (50, y), (450, y), color, thickness)
        zone_layout = [
            [1, 6, 5],
            [2, 3, 4],
            [4, 3, 2],
            [5, 6, 1],
        ]
        for row, zones in enumerate(zone_layout):
            for col, zone in enumerate(zones):
                cv2.putText(
                    canvas,
                    str(zone),
                    (95 + col * 133, 160 + row * 200),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (255, 255, 255),
                    2,
                )

        if len(self.points) == 4:
            src = np.float32(self.points)
            dst = np.float32([[50, 50], [450, 50], [450, 850], [50, 850]])
            matrix = cv2.getPerspectiveTransform(src, dst)
            warped = cv2.warpPerspective(self.frame_bgr, matrix, (500, 900))
            overlay = cv2.addWeighted(warped, 0.82, canvas, 0.18, 0)
            cv2.rectangle(overlay, (50, 50), (450, 850), (255, 255, 255), 3)
            return overlay

        cv2.putText(
            canvas,
            "Seleziona 4 punti per la preview",
            (70, 460),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (220, 220, 220),
            2,
        )
        return canvas


class CropLabelingDialog(QDialog):
    def __init__(
        self,
        crops_dir: str | Path,
        dataset_dir: str | Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Annotazione crop maglie/numeri")
        self.resize(1000, 700)
        self.crops_dir = Path(crops_dir)
        self.dataset_dir = Path(dataset_dir)
        self.image_paths = sorted(
            [
                p
                for p in self.crops_dir.iterdir()
                if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ]
        )
        self.index = 0
        self._build_ui()
        self._load_current_image()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.info = QLabel("Inserisci classe (es. 7, 10, team_home) e salva")
        layout.addWidget(self.info)

        self.image_label = QLabel()
        self.image_label.setMinimumSize(640, 360)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label, 1)

        controls = QHBoxLayout()
        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("Classe, es: 7 oppure team_home")
        prev_btn = QPushButton("Precedente")
        next_btn = QPushButton("Successivo")
        skip_btn = QPushButton("Salta")
        save_btn = QPushButton("Salva classe")
        controls.addWidget(QLabel("Classe"))
        controls.addWidget(self.class_input)
        controls.addWidget(prev_btn)
        controls.addWidget(next_btn)
        controls.addWidget(skip_btn)
        controls.addWidget(save_btn)
        layout.addLayout(controls)

        prev_btn.clicked.connect(self._previous_image)
        next_btn.clicked.connect(self._next_image)
        skip_btn.clicked.connect(self._skip_image)
        save_btn.clicked.connect(self._save_labeled_crop)

    def _load_current_image(self) -> None:
        if not self.image_paths:
            self.info.setText("Nessun crop trovato nella cartella selezionata")
            self.image_label.clear()
            return

        image_path = self.image_paths[self.index]
        pixmap = QPixmap(str(image_path))
        self.image_label.setPixmap(
            pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.info.setText(
            f"Crop {self.index + 1}/{len(self.image_paths)} - file: {image_path.name}"
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._load_current_image()

    def _previous_image(self) -> None:
        if not self.image_paths:
            return
        self.index = max(0, self.index - 1)
        self._load_current_image()

    def _next_image(self) -> None:
        if not self.image_paths:
            return
        self.index = min(len(self.image_paths) - 1, self.index + 1)
        self._load_current_image()

    def _skip_image(self) -> None:
        self._next_image()

    def _save_labeled_crop(self) -> None:
        if not self.image_paths:
            return
        class_name = self.class_input.text().strip()
        if not class_name:
            QMessageBox.warning(
                self, "Classe mancante", "Inserisci una classe prima di salvare"
            )
            return

        source = self.image_paths[self.index]
        target_dir = self.dataset_dir / class_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        shutil.copy2(source, target)
        self.info.setText(f"Salvato: {target}")
        self.class_input.clear()
        self._next_image()


class CourtAnnotationDialog(QDialog):
    def __init__(
        self,
        frames_dir: str | Path,
        dataset_dir: str | Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Annotazione AI campo - 4 keypoint")
        self.resize(1280, 820)
        self.frames_dir = Path(frames_dir)
        self.dataset_dir = Path(dataset_dir)
        self.image_paths = sorted(
            [
                p
                for p in self.frames_dir.iterdir()
                if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ]
        )
        self.index = 0
        self.points: list[list[float]] = []
        self._build_ui()
        self._load_current_image()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.info = QLabel("Clicca 4 punti: alto-sx, alto-dx, basso-dx, basso-sx")
        layout.addWidget(self.info)

        self.image_label = ClickableImageLabel()
        self.image_label.point_added.connect(self._add_point)
        layout.addWidget(self.image_label, 1)

        controls = QHBoxLayout()
        self.split_combo = QComboBox()
        self.split_combo.addItems(["train", "val"])
        prev_btn = QPushButton("Precedente")
        next_btn = QPushButton("Successivo")
        reset_btn = QPushButton("Reset punti")
        save_btn = QPushButton("Salva annotazione")
        controls.addWidget(QLabel("Split"))
        controls.addWidget(self.split_combo)
        controls.addWidget(prev_btn)
        controls.addWidget(next_btn)
        controls.addWidget(reset_btn)
        controls.addWidget(save_btn)
        layout.addLayout(controls)

        prev_btn.clicked.connect(self._previous_image)
        next_btn.clicked.connect(self._next_image)
        reset_btn.clicked.connect(self._reset_points)
        save_btn.clicked.connect(self._save_annotation)

    def _load_current_image(self) -> None:
        if not self.image_paths:
            self.info.setText("Nessun frame trovato nella cartella selezionata")
            return
        image_path = self.image_paths[self.index]
        frame = cv2.imread(str(image_path))
        if frame is None:
            self.info.setText(f"Immagine non leggibile: {image_path}")
            return
        self.frame_shape = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.points = []
        self.image_label.set_image(QPixmap.fromImage(qimg.copy()))
        self.image_label.set_points(self.points)
        self._update_info()

    def _update_info(self) -> None:
        if not self.image_paths:
            return
        self.info.setText(
            f"Frame {self.index + 1}/{len(self.image_paths)} - punti {len(self.points)}/4 - "
            "ordine: alto-sx, alto-dx, basso-dx, basso-sx"
        )

    def _add_point(self, x: float, y: float) -> None:
        if len(self.points) >= 4:
            return
        self.points.append([float(x), float(y)])
        self.image_label.set_points(self.points)
        self._update_info()

    def _reset_points(self) -> None:
        self.points = []
        self.image_label.set_points(self.points)
        self._update_info()

    def _previous_image(self) -> None:
        if not self.image_paths:
            return
        self.index = max(0, self.index - 1)
        self._load_current_image()

    def _next_image(self) -> None:
        if not self.image_paths:
            return
        self.index = min(len(self.image_paths) - 1, self.index + 1)
        self._load_current_image()

    def _save_annotation(self) -> None:
        if len(self.points) != 4:
            QMessageBox.warning(
                self, "Annotazione incompleta", "Devi selezionare esattamente 4 punti"
            )
            return
        image_path = self.image_paths[self.index]
        split = self.split_combo.currentText()
        images_dir = self.dataset_dir / "images" / split
        labels_dir = self.dataset_dir / "labels" / split
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        target_image = images_dir / image_path.name
        shutil.copy2(image_path, target_image)

        h, w = self.frame_shape[:2]
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        x_center = ((x1 + x2) / 2.0) / w
        y_center = ((y1 + y2) / 2.0) / h
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h

        keypoint_values = []
        for x, y in self.points:
            keypoint_values.extend([x / w, y / h, 2])

        label_line = " ".join(
            ["0", f"{x_center:.6f}", f"{y_center:.6f}", f"{bw:.6f}", f"{bh:.6f}"]
            + [
                f"{value:.6f}" if isinstance(value, float) else str(value)
                for value in keypoint_values
            ]
        )
        (labels_dir / f"{image_path.stem}.txt").write_text(
            label_line + "\n", encoding="utf-8"
        )
        self.info.setText(f"Annotazione salvata: {target_image.name} ({split})")
        if self.index < len(self.image_paths) - 1:
            self.index += 1
            self._load_current_image()


from volley_analizer.core.detector import PlayerDetector


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Volley Analyzer - MVP Desktop")
        self.resize(1200, 820)
        self.worker: AnalysisWorker | None = None
        self.config_store = AppConfig()
        # Detector HOG di default, ma aggiornabile da UI
        self.detector = PlayerDetector(
            model_name="yolov8n.pt",  # Placeholder, non usato da HOG
            confidence_threshold=0.25,
            detector_type="hog",
        )
        self._build_ui()
        self._apply_saved_preferences()
        self._build_menus()

    def _apply_saved_preferences(self) -> None:
        prefs = self.config_store.load_preferences()
        if not prefs:
            return
        self.detector_combo.setCurrentText(
            prefs.get("detector", self.detector_combo.currentText())
        )
        self.model_input.setText(prefs.get("model", self.model_input.text()))
        self.segmentation_cb.setChecked(
            bool(prefs.get("segmentation", self.segmentation_cb.isChecked()))
        )
        self.hw_accel_cb.setChecked(
            bool(prefs.get("hw_accel", self.hw_accel_cb.isChecked()))
        )
        self.sample_spin.setValue(
            int(prefs.get("sample_every", self.sample_spin.value()))
        )
        self.chunk_spin.setValue(
            int(prefs.get("chunk_seconds", self.chunk_spin.value()))
        )
        self.jersey_classifier_input.setText(prefs.get("jersey_classifier", ""))
        self._update_active_model_label()

    def _update_active_model_label(self, model_path: str | None = None) -> None:
        if not hasattr(self, "active_model_label"):
            return

        if model_path is None:
            use_seg = self.segmentation_cb.isChecked()
            model_path = self._resolve_detector_model(self.model_input.text(), use_seg)

        model_name = Path(model_path).name if model_path else "-"
        mode = "seg" if self.segmentation_cb.isChecked() else "detect/hog"
        self.active_model_label.setText(f"Detector attivo: {model_name} ({mode})")

        default_models = {
            "yolov8n.pt",
            "yolov8s.pt",
            "yolov8m.pt",
            "yolov8l.pt",
            "yolov8x.pt",
            "yolov8n-seg.pt",
            "yolov8s-seg.pt",
            "yolov8m-seg.pt",
            "yolov8l-seg.pt",
            "yolov8x-seg.pt",
        }

        if model_name == "-":
            bg = "#6b7280"  # grigio
        elif self.detector_combo.currentText() == "hog":
            bg = "#4f46e5"  # indigo
        elif model_name in default_models:
            bg = "#f59e0b"  # arancione (default)
        else:
            bg = "#16a34a"  # verde (custom/best.pt)

        self.active_model_label.setStyleSheet(
            f"QLabel {{ background-color: {bg}; color: white; padding: 6px 10px; border-radius: 8px; font-weight: 600; }}"
        )

    def _build_menus(self) -> None:
        menu_bar = self.menuBar()

        analysis_menu = menu_bar.addMenu("Analisi")

        calibrate_action = QAction("Calibra campo (manuale)...", self)
        calibrate_action.triggered.connect(self._open_calibration)
        analysis_menu.addAction(calibrate_action)

        ai_field_action = QAction("Calibra campo con AI...", self)
        ai_field_action.triggered.connect(self._detect_field_with_ai)
        analysis_menu.addAction(ai_field_action)

        analysis_menu.addSeparator()
        split_action = QAction("Dividi video in segmenti...", self)
        split_action.triggered.connect(self._split_video_dialog)
        analysis_menu.addAction(split_action)

        analyze_segments_action = QAction("Analizza tutti i segmenti", self)
        analyze_segments_action.triggered.connect(self._analyze_all_segments)
        analysis_menu.addAction(analyze_segments_action)

        analysis_menu.addSeparator()
        start_action = QAction("Avvia analisi", self)
        start_action.triggered.connect(self._start_analysis)
        analysis_menu.addAction(start_action)

        stop_action = QAction("Interrompi analisi", self)
        stop_action.triggered.connect(self._stop_analysis)
        analysis_menu.addAction(stop_action)

        models_menu = menu_bar.addMenu("Modelli AI")

        players_menu = models_menu.addMenu("Giocatori (YOLO)")
        prepare_yolo_action = QAction("Prepara dataset da video...", self)
        prepare_yolo_action.triggered.connect(self._open_prepare_yolo_dataset_dialog)
        players_menu.addAction(prepare_yolo_action)

        data_yaml_action = QAction("Genera data.yaml...", self)
        data_yaml_action.triggered.connect(self._open_generate_data_yaml_dialog)
        players_menu.addAction(data_yaml_action)

        train_yolo_action = QAction("Addestra modello giocatori...", self)
        train_yolo_action.triggered.connect(self._open_train_yolo_dialog)
        players_menu.addAction(train_yolo_action)

        jersey_menu = models_menu.addMenu("Maglie e numeri")
        extract_crops_action = QAction("Estrai crop giocatori...", self)
        extract_crops_action.triggered.connect(self._open_extract_crops_dialog)
        jersey_menu.addAction(extract_crops_action)

        label_crops_action = QAction("Etichetta crop dentro app...", self)
        label_crops_action.triggered.connect(self._open_label_crops_dialog)
        jersey_menu.addAction(label_crops_action)

        train_jersey_action = QAction("Addestra classificatore maglie/numeri...", self)
        train_jersey_action.triggered.connect(self._open_train_jersey_dialog)
        jersey_menu.addAction(train_jersey_action)

        court_menu = models_menu.addMenu("Campo (keypoints)")
        extract_court_frames_action = QAction("Estrai frame campo...", self)
        extract_court_frames_action.triggered.connect(
            self._open_extract_court_frames_dialog
        )
        court_menu.addAction(extract_court_frames_action)

        annotate_court_action = QAction("Annota campo dentro app...", self)
        annotate_court_action.triggered.connect(self._open_court_annotation_dialog)
        court_menu.addAction(annotate_court_action)

        train_court_action = QAction("Addestra modello campo...", self)
        train_court_action.triggered.connect(self._open_train_court_dialog)
        court_menu.addAction(train_court_action)

        models_menu.addSeparator()
        use_prefs_action = QAction("Seleziona modelli attivi (Preferenze)...", self)
        use_prefs_action.triggered.connect(self._open_preferences_dialog)
        models_menu.addAction(use_prefs_action)

        report_menu = menu_bar.addMenu("Report")
        zone_report_action = QAction("Genera report zone...", self)
        zone_report_action.triggered.connect(self._generate_zone_report)
        report_menu.addAction(zone_report_action)

        open_report_action = QAction("Apri report...", self)
        open_report_action.triggered.connect(self._open_report_dialog)
        report_menu.addAction(open_report_action)

        app_menu = menu_bar.addMenu("Applicazione")
        preferences_action = QAction("Preferenze...", self)
        preferences_action.triggered.connect(self._open_preferences_dialog)
        app_menu.addAction(preferences_action)

    def _open_preferences_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferenze applicazione")
        layout = QFormLayout(dialog)

        detector_combo = QComboBox()
        detector_combo.addItems(["yolo", "hog"])
        detector_combo.setCurrentText(self.detector_combo.currentText())

        model_input = QLineEdit(self.model_input.text())
        model_row = QHBoxLayout()
        model_browse_btn = QPushButton("Sfoglia")
        model_row.addWidget(model_input)
        model_row.addWidget(model_browse_btn)

        segmentation_cb = QCheckBox("Usa instance segmentation YOLOv8-seg")
        segmentation_cb.setChecked(self.segmentation_cb.isChecked())
        hw_accel_cb = QCheckBox("Usa accelerazione hardware")
        hw_accel_cb.setChecked(self.hw_accel_cb.isChecked())
        sample_spin = QSpinBox()
        sample_spin.setRange(1, 60)
        sample_spin.setValue(self.sample_spin.value())
        chunk_spin = QSpinBox()
        chunk_spin.setRange(10, 600)
        chunk_spin.setValue(self.chunk_spin.value())
        jersey_input = QLineEdit(self.jersey_classifier_input.text())
        jersey_row = QHBoxLayout()
        jersey_browse_btn = QPushButton("Sfoglia")
        jersey_row.addWidget(jersey_input)
        jersey_row.addWidget(jersey_browse_btn)

        def browse_yolo_model():
            path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Scegli modello YOLO",
                str(Path.cwd()),
                "Modelli PyTorch (*.pt);;Tutti i file (*)",
            )
            if path:
                model_input.setText(path)

        def browse_jersey_classifier():
            path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Scegli classificatore maglia",
                str(Path.cwd()),
                "Checkpoint PyTorch (*.pt);;Tutti i file (*)",
            )
            if path:
                jersey_input.setText(path)

        model_browse_btn.clicked.connect(browse_yolo_model)
        jersey_browse_btn.clicked.connect(browse_jersey_classifier)

        layout.addRow("Detector predefinito", detector_combo)
        layout.addRow("Modello YOLO", self._wrap_layout(model_row))
        layout.addRow("Segmentazione", segmentation_cb)
        layout.addRow("Hardware accel", hw_accel_cb)
        layout.addRow("Sample every N frame", sample_spin)
        layout.addRow("Chunk analisi (sec)", chunk_spin)
        layout.addRow("Classificatore maglia", self._wrap_layout(jersey_row))

        badge_legend = QLabel(
            "Legenda badge detector: "
            "<span style='background:#16a34a;color:white;padding:2px 6px;border-radius:6px;'>Verde = modello custom</span> "
            "<span style='background:#f59e0b;color:white;padding:2px 6px;border-radius:6px;'>Arancione = modello default</span> "
            "<span style='background:#4f46e5;color:white;padding:2px 6px;border-radius:6px;'>Indaco = HOG</span>"
        )
        badge_legend.setWordWrap(True)
        layout.addRow(badge_legend)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Salva")
        cancel_btn = QPushButton("Annulla")
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

        cancel_btn.clicked.connect(dialog.reject)

        def save_preferences():
            self.detector_combo.setCurrentText(detector_combo.currentText())
            self.model_input.setText(model_input.text().strip() or "yolov8n.pt")
            self.segmentation_cb.setChecked(segmentation_cb.isChecked())
            self.hw_accel_cb.setChecked(hw_accel_cb.isChecked())
            self.sample_spin.setValue(sample_spin.value())
            self.chunk_spin.setValue(chunk_spin.value())
            self.jersey_classifier_input.setText(jersey_input.text().strip())
            self._update_active_model_label(self.model_input.text().strip())
            self.config_store.save_preferences(
                {
                    "detector": self.detector_combo.currentText(),
                    "model": self.model_input.text().strip() or "yolov8n.pt",
                    "segmentation": self.segmentation_cb.isChecked(),
                    "hw_accel": self.hw_accel_cb.isChecked(),
                    "sample_every": self.sample_spin.value(),
                    "chunk_seconds": self.chunk_spin.value(),
                    "jersey_classifier": self.jersey_classifier_input.text().strip(),
                }
            )
            self._append_log("Preferenze applicazione aggiornate")
            dialog.accept()

        save_btn.clicked.connect(save_preferences)
        dialog.exec()

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def _resolve_detector_model(
        self, model_name: str, use_instance_segmentation: bool
    ) -> str:
        model_name = (model_name or "").strip()
        if not model_name:
            return "yolov8n-seg.pt" if use_instance_segmentation else "yolov8n.pt"

        if use_instance_segmentation:
            defaults = {
                "yolov8n.pt": "yolov8n-seg.pt",
                "yolov8s.pt": "yolov8s-seg.pt",
                "yolov8m.pt": "yolov8m-seg.pt",
                "yolov8l.pt": "yolov8l-seg.pt",
                "yolov8x.pt": "yolov8x-seg.pt",
            }
            return defaults.get(model_name, model_name)

        return model_name

    def _run_training_command(self, command: list[str]) -> None:
        self._append_log("Avvio operazione addestramento...")
        self.command_worker = CommandWorker(command, cwd=str(self._project_root()))
        self.command_worker.log_message.connect(self._append_log)
        self.command_worker.finished_success.connect(lambda msg: self._append_log(msg))
        self.command_worker.finished_error.connect(
            lambda msg: QMessageBox.critical(self, "Errore addestramento", msg)
        )
        self.command_worker.finished_error.connect(self._append_log)
        self.command_worker.start()

    def _browse_file_into(
        self, target: QLineEdit, title: str, file_filter: str
    ) -> None:
        path, _ = QFileDialog.getOpenFileName(self, title, str(Path.cwd()), file_filter)
        if path:
            target.setText(path)

    def _browse_dir_into(self, target: QLineEdit, title: str) -> None:
        path = QFileDialog.getExistingDirectory(self, title, str(Path.cwd()))
        if path:
            target.setText(path)

    def _open_label_crops_dialog(self) -> None:
        default_crops = self._project_root() / "data" / "jersey_crops" / "unlabeled"
        crops_dir = QFileDialog.getExistingDirectory(
            self,
            "Scegli cartella crop da etichettare",
            str(default_crops if default_crops.exists() else self._project_root()),
        )
        if not crops_dir:
            return

        dataset_dir = QFileDialog.getExistingDirectory(
            self,
            "Scegli cartella dataset target (verranno create le cartelle classe)",
            str(self._project_root() / "data" / "jersey_dataset"),
        )
        if not dataset_dir:
            return

        dialog = CropLabelingDialog(crops_dir, dataset_dir, self)
        dialog.exec()

    def _open_extract_crops_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Estrai crop giocatori")
        form = QFormLayout(dialog)
        video = QLineEdit(self.video_input.text())
        output = QLineEdit("data/jersey_crops/unlabeled")
        model = QLineEdit(self.model_input.text() or "yolov8n-seg.pt")
        seg = QCheckBox("Usa YOLOv8-seg")
        seg.setChecked(True)
        sample = QSpinBox()
        sample.setRange(1, 300)
        sample.setValue(10)
        conf = QDoubleSpinBox()
        conf.setRange(0.05, 1.0)
        conf.setSingleStep(0.05)
        conf.setValue(0.25)
        form.addRow("Video", video)
        form.addRow("Output crop", output)
        form.addRow("Modello", model)
        form.addRow("Segmentazione", seg)
        form.addRow("Sample every", sample)
        form.addRow("Confidenza", conf)
        run_btn = QPushButton("Avvia estrazione")
        form.addRow(run_btn)

        def run():
            cmd = [
                sys.executable,
                "scripts/extract_player_crops_for_classifier.py",
                video.text().strip(),
                "--output",
                output.text().strip(),
                "--model",
                model.text().strip(),
                "--sample-every",
                str(sample.value()),
                "--conf",
                str(conf.value()),
            ]
            if seg.isChecked():
                cmd.append("--seg")
            dialog.accept()
            self._run_training_command(cmd)

        run_btn.clicked.connect(run)
        dialog.exec()

    def _open_generate_data_yaml_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Genera data.yaml YOLO")
        form = QFormLayout(dialog)
        dataset = QLineEdit("data/volley_yolo")
        classes = QLineEdit("player,number")
        output = QLineEdit("")
        form.addRow("Dataset dir", dataset)
        form.addRow("Classi", classes)
        form.addRow("Output opzionale", output)
        run_btn = QPushButton("Genera")
        form.addRow(run_btn)

        def run():
            cmd = [
                sys.executable,
                "scripts/generate_yolo_data_yaml.py",
                dataset.text().strip(),
                "--classes",
                classes.text().strip(),
            ]
            if output.text().strip():
                cmd.extend(["--output", output.text().strip()])
            dialog.accept()
            self._run_training_command(cmd)

        run_btn.clicked.connect(run)
        dialog.exec()

    def _open_prepare_yolo_dataset_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Crea dataset YOLO da video")
        form = QFormLayout(dialog)
        video = QLineEdit(self.video_input.text())
        output = QLineEdit("data/volley_yolo")
        model = QLineEdit(self.model_input.text() or "yolov8n.pt")
        conf = QDoubleSpinBox()
        conf.setRange(0.05, 1.0)
        conf.setSingleStep(0.05)
        conf.setValue(0.35)
        sample = QSpinBox()
        sample.setRange(1, 1000)
        sample.setValue(30)
        max_frames = QSpinBox()
        max_frames.setRange(1, 10000)
        max_frames.setValue(1000)
        form.addRow("Video", video)
        form.addRow("Output dataset", output)
        form.addRow("Modello pseudo-label", model)
        form.addRow("Confidenza", conf)
        form.addRow("Sample every", sample)
        form.addRow("Max frame", max_frames)
        run_btn = QPushButton("Crea dataset")
        form.addRow(run_btn)

        def run():
            cmd = [
                sys.executable,
                "scripts/prepare_yolo_dataset_from_video.py",
                video.text().strip(),
                "--output",
                output.text().strip(),
                "--model",
                model.text().strip(),
                "--conf",
                str(conf.value()),
                "--sample-every",
                str(sample.value()),
                "--max-frames",
                str(max_frames.value()),
            ]
            dialog.accept()
            self._run_training_command(cmd)

        run_btn.clicked.connect(run)
        dialog.exec()

    def _open_train_yolo_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Addestra YOLO detect/segment")
        form = QFormLayout(dialog)
        data = QLineEdit("data/volley_yolo/data.yaml")
        model = QLineEdit("yolov8n.pt")
        task = QComboBox()
        task.addItems(["detect", "segment"])
        epochs = QSpinBox()
        epochs.setRange(1, 500)
        epochs.setValue(50)
        imgsz = QSpinBox()
        imgsz.setRange(320, 1920)
        imgsz.setValue(640)
        batch = QSpinBox()
        batch.setRange(1, 128)
        batch.setValue(8)
        form.addRow("data.yaml", data)
        form.addRow("Modello base", model)
        form.addRow("Task", task)
        form.addRow("Epochs", epochs)
        form.addRow("Image size", imgsz)
        form.addRow("Batch", batch)
        run_btn = QPushButton("Avvia training YOLO")
        form.addRow(run_btn)

        def run():
            cmd = [
                sys.executable,
                "scripts/train_yolo_custom.py",
                "--data",
                data.text().strip(),
                "--model",
                model.text().strip(),
                "--task",
                task.currentText(),
                "--epochs",
                str(epochs.value()),
                "--imgsz",
                str(imgsz.value()),
                "--batch",
                str(batch.value()),
            ]
            dialog.accept()
            self._run_training_command(cmd)

        run_btn.clicked.connect(run)
        dialog.exec()

    def _open_train_jersey_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Addestra classificatore maglia/team")
        form = QFormLayout(dialog)
        dataset = QLineEdit("data/jersey_dataset")
        output = QLineEdit("models/jersey_classifier.pt")
        epochs = QSpinBox()
        epochs.setRange(1, 300)
        epochs.setValue(30)
        batch = QSpinBox()
        batch.setRange(1, 256)
        batch.setValue(32)

        helper = QLabel(
            "Flusso consigliato: 1) Estrai crop  2) Etichetta crop dentro app  3) Avvia training"
        )
        quick_actions = QHBoxLayout()
        extract_btn = QPushButton("1) Estrai crop")
        label_btn = QPushButton("2) Etichetta crop")
        quick_actions.addWidget(extract_btn)
        quick_actions.addWidget(label_btn)

        form.addRow(helper)
        form.addRow(self._wrap_layout(quick_actions))
        form.addRow("Dataset classi", dataset)
        form.addRow("Output checkpoint", output)
        form.addRow("Epochs", epochs)
        form.addRow("Batch", batch)
        run_btn = QPushButton("3) Avvia training classificatore")
        form.addRow(run_btn)

        def run():
            cmd = [
                sys.executable,
                "scripts/train_jersey_classifier.py",
                dataset.text().strip(),
                "--output",
                output.text().strip(),
                "--epochs",
                str(epochs.value()),
                "--batch",
                str(batch.value()),
            ]
            dialog.accept()
            self._run_training_command(cmd)

        extract_btn.clicked.connect(lambda: self._open_extract_crops_dialog())
        label_btn.clicked.connect(lambda: self._open_label_crops_dialog())
        run_btn.clicked.connect(run)
        dialog.exec()

    def _open_extract_court_frames_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Estrai frame per AI campo")
        form = QFormLayout(dialog)
        video = QLineEdit(self.video_input.text())
        output = QLineEdit("data/court_keypoints/raw_frames")
        sample = QSpinBox()
        sample.setRange(1, 1000)
        sample.setValue(90)
        max_frames = QSpinBox()
        max_frames.setRange(1, 5000)
        max_frames.setValue(300)
        form.addRow("Video", video)
        form.addRow("Output frame", output)
        form.addRow("Sample every", sample)
        form.addRow("Max frame", max_frames)
        run_btn = QPushButton("Estrai frame")
        form.addRow(run_btn)

        def run():
            cmd = [
                sys.executable,
                "scripts/extract_frames_for_court_annotation.py",
                video.text().strip(),
                "--output",
                output.text().strip(),
                "--sample-every",
                str(sample.value()),
                "--max-frames",
                str(max_frames.value()),
            ]
            dialog.accept()
            self._run_training_command(cmd)

        run_btn.clicked.connect(run)
        dialog.exec()

    def _open_court_annotation_dialog(self) -> None:
        default_frames = (
            self._project_root() / "data" / "court_keypoints" / "raw_frames"
        )
        frames_dir = QFileDialog.getExistingDirectory(
            self,
            "Scegli cartella frame da annotare",
            str(default_frames if default_frames.exists() else self._project_root()),
        )
        if not frames_dir:
            return
        dataset_dir = self._project_root() / "data" / "court_keypoints"
        dialog = CourtAnnotationDialog(frames_dir, dataset_dir, self)
        dialog.exec()

    def _open_train_court_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Addestra AI campo/keypoints")
        form = QFormLayout(dialog)
        data = QLineEdit("data/court_keypoints/data.yaml")
        model = QLineEdit("yolov8n-pose.pt")
        epochs = QSpinBox()
        epochs.setRange(1, 500)
        epochs.setValue(80)
        imgsz = QSpinBox()
        imgsz.setRange(320, 1920)
        imgsz.setValue(960)
        batch = QSpinBox()
        batch.setRange(1, 128)
        batch.setValue(8)
        form.addRow("data.yaml keypoints", data)
        form.addRow("Modello base", model)
        form.addRow("Epochs", epochs)
        form.addRow("Image size", imgsz)
        form.addRow("Batch", batch)
        run_btn = QPushButton("Avvia training campo")
        form.addRow(run_btn)

        def run():
            cmd = [
                sys.executable,
                "scripts/train_court_keypoints.py",
                "--data",
                data.text().strip(),
                "--model",
                model.text().strip(),
                "--epochs",
                str(epochs.value()),
                "--imgsz",
                str(imgsz.value()),
                "--batch",
                str(batch.value()),
            ]
            dialog.accept()
            self._run_training_command(cmd)

        run_btn.clicked.connect(run)
        dialog.exec()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        form = QFormLayout()

        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(
            ["File Locale", "Stream IP (RTSP/RTMP/HTTP)", "Webcam"]
        )
        self.source_type_combo.currentIndexChanged.connect(self._on_source_type_changed)

        self.webcam_combo = QComboBox()
        self.webcam_combo.setVisible(False)
        self.webcam_combo.currentIndexChanged.connect(self._on_webcam_changed)

        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self._update_preview)
        self.preview_cap = None
        self.preview_frames_left: int | None = None

        self.video_input = QLineEdit()
        self.video_input.setPlaceholderText("Percorso file locale o URL stream")
        self.video_input.editingFinished.connect(self._on_video_input_changed)

        self.browse_video_btn = QPushButton("Scegli file video...")
        self.browse_video_btn.clicked.connect(self._select_video)

        self.play_preview_btn = QPushButton("▶ Anteprima 3s")
        self.play_preview_btn.clicked.connect(self._play_local_preview_clip)

        self.hw_accel_cb = QCheckBox("Usa Accelerazione Hardware (NVDEC NVIDIA)")
        self.hw_accel_cb.setChecked(True)
        self.hw_accel_cb.setToolTip(
            "Migliora le performance usando la GPU per decodificare il video. Disabilita se hai problemi."
        )

        self.output_input = QLineEdit(str((Path.cwd() / "output").resolve()))

        self.split_video_btn = QPushButton("Splitta video")
        self.split_video_btn.clicked.connect(self._split_video_dialog)

        self.analyze_segments_btn = QPushButton("Analizza tutti i segmenti")
        self.analyze_segments_btn.clicked.connect(self._analyze_all_segments)

        browse_output_btn = QPushButton("Sfoglia output")
        browse_output_btn.clicked.connect(self._select_output_dir)

        calibrate_btn = QPushButton("Calibra campo")
        calibrate_btn.clicked.connect(self._open_calibration)

        video_row = QHBoxLayout()
        video_row.addWidget(self.source_type_combo)
        video_row.addWidget(self.video_input)
        video_row.addWidget(self.browse_video_btn)
        video_row.addWidget(self.play_preview_btn)
        video_row.addWidget(self.webcam_combo)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_input)
        output_row.addWidget(browse_output_btn)

        self.sample_spin = QSpinBox()
        self.sample_spin.setRange(1, 60)
        self.sample_spin.setValue(3)

        self.conf_spin = QDoubleSpinBox()
        self.conf_spin.setRange(0.05, 1.0)
        self.conf_spin.setSingleStep(0.05)
        self.conf_spin.setValue(0.25)

        self.chunk_spin = QSpinBox()
        self.chunk_spin.setRange(10, 600)
        self.chunk_spin.setValue(60)

        self.detector_combo = QComboBox()
        self.detector_combo.addItems(["yolo", "hog"])
        self.detector_combo.setCurrentText("hog")  # HOG come default

        self.model_input = QLineEdit("yolov8n.pt")
        self.segmentation_cb = QCheckBox("Usa instance segmentation YOLOv8-seg")
        self.segmentation_cb.setToolTip(
            "Usa un modello YOLOv8-seg per separare persone sovrapposte tramite maschere instance."
        )
        self.segmentation_cb.stateChanged.connect(self._on_segmentation_changed)
        self.jersey_classifier_input = QLineEdit("")
        self.jersey_classifier_input.setPlaceholderText(
            "models/jersey_classifier.pt (opzionale)"
        )
        self.calibration_label = QLabel(self._calibration_summary())

        form.addRow("Sorgente Video", self._wrap_layout(video_row))
        form.addRow("Output", self._wrap_layout(output_row))
        form.addRow("Punti campo", self.calibration_label)
        main_layout.addLayout(form)

        # Nascondi il campo YOLO model se serve
        self.form = form
        self.detector_combo.currentTextChanged.connect(self._on_detector_changed)
        self._on_detector_changed(self.detector_combo.currentText())
        self._update_active_model_label()

        # Layout orizzontale per i pulsanti principali
        button_layout_main = QHBoxLayout()
        self.run_button = QPushButton("Avvia analisi")
        self.run_button.clicked.connect(self._start_analysis)
        button_layout_main.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._stop_analysis)
        button_layout_main.addWidget(self.stop_button)

        main_layout.addLayout(button_layout_main)

        self.status_label = QLabel("Pronto")
        main_layout.addWidget(self.status_label)

        self.active_model_label = QLabel("Detector attivo: -")
        main_layout.addWidget(self.active_model_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        main_layout.addWidget(self.progress)

        stats_layout = QHBoxLayout()
        self.frame_label = QLabel("Frame: -")
        self.time_label = QLabel("Tempo: -")
        self.detection_label = QLabel("Detection: -")
        self.track_label = QLabel("Track: -")
        stats_layout.addWidget(self.frame_label)
        stats_layout.addWidget(self.time_label)
        stats_layout.addWidget(self.detection_label)
        stats_layout.addWidget(self.track_label)
        main_layout.addLayout(stats_layout)

        content_layout = QGridLayout()
        self.preview_label = QLabel("Anteprima analisi")
        self.preview_label.setMinimumSize(720, 405)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #202020; color: #dddddd;")
        content_layout.addWidget(QLabel("Preview live tracking"), 0, 0)
        content_layout.addWidget(self.preview_label, 1, 0)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        content_layout.addWidget(QLabel("Log analisi"), 0, 1)
        content_layout.addWidget(self.log_output, 1, 1)
        main_layout.addLayout(content_layout, 1)

    def _on_webcam_changed(self, index: int):
        if self.source_type_combo.currentIndex() == 2:
            device_id = self.webcam_combo.currentData()
            if device_id is not None and device_id != -1:
                self._start_preview(device_id)

    def _start_preview(self, source):
        self._stop_preview()
        self.preview_cap = cv2.VideoCapture(source)
        self.preview_frames_left = None
        if self.preview_cap.isOpened():
            self.preview_timer.start(33)
        else:
            self.preview_label.setText("Impossibile aprire la webcam")

    def _stop_preview(self):
        self.preview_timer.stop()
        self.preview_frames_left = None
        if hasattr(self, "preview_cap") and self.preview_cap is not None:
            self.preview_cap.release()
            self.preview_cap = None

    def _update_preview(self):
        if (
            hasattr(self, "preview_cap")
            and self.preview_cap
            and self.preview_cap.isOpened()
        ):
            ret, frame = self.preview_cap.read()
            if not ret:
                self._stop_preview()
                return
            if ret:
                # Aggiorna detector in base alla UI
                detector_type = self.detector_combo.currentText()
                confidence = self.conf_spin.value()
                use_seg = self.segmentation_cb.isChecked()
                model_name = self._resolve_detector_model(
                    self.model_input.text(), use_seg
                )
                if use_seg:
                    detector_type = "yolo"
                if (
                    self.detector.detector_type != detector_type
                    or self.detector.confidence_threshold != confidence
                    or (
                        detector_type == "yolo"
                        and self.detector.model_name != model_name
                    )
                ):
                    self.detector = PlayerDetector(
                        model_name=model_name,
                        confidence_threshold=confidence,
                        detector_type=detector_type,
                    )
                # Esegui detection
                detections = self.detector.detect(frame)
                print(
                    f"DEBUG: trovate {len(detections)} detection con detector {detector_type} e conf {confidence}"
                )
                # Disegna maschere e bounding box
                for det in detections:
                    mask = getattr(det, "mask", None)
                    if mask is not None:
                        try:
                            mask_bool = mask.astype(bool)
                            if mask_bool.shape[:2] != frame.shape[:2]:
                                mask_bool = cv2.resize(
                                    mask_bool.astype("uint8"),
                                    (frame.shape[1], frame.shape[0]),
                                    interpolation=cv2.INTER_NEAREST,
                                ).astype(bool)
                            overlay = frame.copy()
                            overlay[mask_bool] = (0, 140, 255)
                            blended = cv2.addWeighted(frame, 0.65, overlay, 0.35, 0)
                            frame[mask_bool] = blended[mask_bool]
                        except Exception as exc:
                            print(
                                f"[DEBUG] Impossibile disegnare maschera preview: {exc}"
                            )
                    x1, y1, x2, y2 = map(int, det.bbox)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    if hasattr(det, "confidence"):
                        cv2.putText(
                            frame,
                            f"{det.confidence:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            1,
                            cv2.LINE_AA,
                        )
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                self.preview_label.setPixmap(
                    pixmap.scaled(
                        self.preview_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

                if self.preview_frames_left is not None:
                    self.preview_frames_left -= 1
                    if self.preview_frames_left <= 0:
                        self._stop_preview()

    def _on_source_type_changed(self, index: int):
        self._stop_preview()

        is_local = index == 0
        is_webcam = index == 2

        self.browse_video_btn.setVisible(is_local)
        self.play_preview_btn.setVisible(is_local)
        self.split_video_btn.setVisible(is_local)
        self.analyze_segments_btn.setVisible(is_local)

        self.video_input.setVisible(not is_webcam)
        self.webcam_combo.setVisible(is_webcam)

        if index == 1:
            self.preview_label.clear()
            self.preview_label.setText("Preview live tracking")
            self.video_input.setPlaceholderText(
                "Inserisci URL (es. rtsp://192.168.1.100/stream)"
            )
        elif index == 2:
            self.preview_label.clear()
            self.preview_label.setText("Preview live tracking")
            self._populate_webcams()
            self._on_webcam_changed(self.webcam_combo.currentIndex())
        else:
            self.video_input.setPlaceholderText("Seleziona file video da analizzare")
            current = self.video_input.text().strip()
            if current:
                self._show_local_video_thumbnail(current)
            else:
                self.preview_label.clear()
                self.preview_label.setText(
                    "Seleziona un file video per vedere l'anteprima"
                )

    def _populate_webcams(self):
        if self.webcam_combo.count() > 0:
            return  # Già popolata

        self.webcam_combo.clear()
        self.webcam_combo.addItem("Ricerca webcam in corso...", -1)
        QApplication.processEvents()

        self.webcam_combo.clear()
        found = False
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.webcam_combo.addItem(f"Webcam {i} ({w}x{h})", i)
                cap.release()
                found = True

        if not found:
            self.webcam_combo.addItem("Nessuna webcam trovata", -1)

    def _on_detector_changed(self, text):
        # Le preferenze detector/modello sono gestite dal menu Applicazione > Preferenze.
        self._update_active_model_label()
        return

    def _on_segmentation_changed(self, _state=None):
        if self.segmentation_cb.isChecked():
            self.detector_combo.setCurrentText("yolo")
            resolved = self._resolve_detector_model(self.model_input.text(), True)
            self.model_input.setText(resolved)
            self._append_log(f"Instance segmentation abilitata: modello {resolved}")
        self._update_active_model_label(self.model_input.text().strip())
        self._on_detector_changed(self.detector_combo.currentText())

    def _split_video_dialog(self):
        # Assicurati che sia file locale
        if self.source_type_combo.currentIndex() != 0:
            QMessageBox.warning(
                self,
                "Errore",
                "La divisione è supportata solo per i file video locali.",
            )
            return

        video_path = self.video_input.text().strip()
        if not video_path or not os.path.isfile(video_path):
            QMessageBox.warning(
                self, "Errore", "Seleziona prima un file video valido da splittare."
            )
            return

        # Dialog personalizzato per il tempo di split
        from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout
        from PyQt6.QtWidgets import QPushButton as QB

        dialog = QDialog(self)
        dialog.setWindowTitle("Configura Split Video")
        dialog.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        # Etichetta
        label = QLabel("Seleziona la durata di ogni segmento (minuti):")
        layout.addWidget(label)

        # SpinBox per minuti
        spin = QSpinBox()
        spin.setRange(1, 60)
        spin.setValue(2)  # Default 2 minuti
        spin.setSuffix(" minuti")
        layout.addWidget(spin)

        # Pulsanti
        button_layout = QHBoxLayout()

        ok_btn = QB("Split")
        ok_btn.clicked.connect(lambda: dialog.done(spin.value()))
        button_layout.addWidget(ok_btn)

        cancel_btn = QB("Annulla")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        # Esegui dialog
        result = dialog.exec()
        if result == 0:
            return  # Annullato

        seconds = result * 60  # Converti minuti in secondi

        base, ext = os.path.splitext(video_path)
        output_pattern = f"{base}_split_%03d{ext}"
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-c",
            "copy",
            "-map",
            "0",
            "-segment_time",
            str(seconds),
            "-f",
            "segment",
            "-reset_timestamps",
            "1",
            output_pattern,
        ]
        try:
            subprocess.run(cmd, check=True)
            # Trova i file creati
            created = sorted(
                [
                    f
                    for f in os.listdir(os.path.dirname(video_path) or ".")
                    if f.startswith(os.path.basename(base) + "_split_")
                    and f.endswith(ext)
                ]
            )
            QMessageBox.information(
                self,
                "Split completato",
                f"Video splittato in {len(created)} file ({result} minuti ciascuno):\n"
                + "\n".join(created),
            )
            self._append_log(
                f"Video splittato: {len(created)} segmenti di {result} minuti"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Errore split", f"Errore durante lo split del video:\n{e}"
            )
            self._append_log(f"Errore durante lo split: {e}")

    def _analyze_all_segments(self):
        # Assicurati che sia file locale
        if self.source_type_combo.currentIndex() != 0:
            QMessageBox.warning(
                self,
                "Errore",
                "L'analisi a segmenti è supportata solo per i file video locali.",
            )
            return

        video_path = self.video_input.text().strip()
        if not video_path or not os.path.isfile(video_path):
            QMessageBox.warning(self, "Errore", "Seleziona prima un file video valido.")
            return
        base, ext = os.path.splitext(video_path)
        folder = os.path.dirname(video_path) or "."
        segment_files = sorted(
            [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.startswith(os.path.basename(base) + "_split_") and f.endswith(ext)
            ]
        )
        if not segment_files:
            QMessageBox.warning(
                self,
                "Nessun segmento",
                "Non sono stati trovati segmenti split nella cartella del video.",
            )
            return
        detector_type = self.detector_combo.currentText()
        use_instance_segmentation = self.segmentation_cb.isChecked()
        detector_model = self._resolve_detector_model(
            self.model_input.text(), use_instance_segmentation
        )
        if use_instance_segmentation:
            detector_type = "yolo"
        output_dir = self.output_input.text().strip() or str(
            (Path.cwd() / "output").resolve()
        )
        errors = []
        for seg in segment_files:
            try:
                config = PipelineConfig(
                    video_path=seg,
                    output_dir=output_dir,
                    sample_every_n_frames=self.sample_spin.value(),
                    detector_model=detector_model,
                    detector_confidence=self.conf_spin.value(),
                    field_points=self.config_store.load_field_points(),
                    detector_type=detector_type,
                    use_instance_segmentation=use_instance_segmentation,
                    jersey_classifier_model=self.jersey_classifier_input.text().strip()
                    or None,
                )
                pipeline = VolleyballAnalysisPipeline(config)
                pipeline.run_chunked(chunk_seconds=self.chunk_spin.value())
            except Exception as e:
                errors.append(f"{os.path.basename(seg)}: {e}")
        # Unione automatica dei CSV
        import csv
        import glob

        merged_files = []
        for csv_name in ["tracks.csv", "summary.csv"]:
            csv_paths = [
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith("tracks") or f.startswith("summary")
            ]
            csv_paths = [
                f
                for f in csv_paths
                if os.path.basename(f).startswith(csv_name.split(".")[0])
                and f.endswith(csv_name)
            ]
            if not csv_paths:
                continue
            merged_path = os.path.join(
                output_dir, csv_name.replace(".csv", "_merged.csv")
            )
            with open(merged_path, "w", newline="") as fout:
                writer = None
                for i, path in enumerate(sorted(csv_paths)):
                    with open(path, "r", newline="") as fin:
                        reader = csv.reader(fin)
                        header = next(reader)
                        if writer is None:
                            writer = csv.writer(fout)
                            writer.writerow(header)
                        for row in reader:
                            writer.writerow(row)
            merged_files.append(merged_path)
        if errors:
            QMessageBox.warning(
                self,
                "Analisi segmenti terminata con errori",
                "Alcuni segmenti non sono stati analizzati:\n"
                + "\n".join(errors)
                + (
                    f"\n\nFile CSV uniti:\n" + "\n".join(merged_files)
                    if merged_files
                    else ""
                ),
            )
        else:
            QMessageBox.information(
                self,
                "Analisi segmenti completata",
                f"Tutti i segmenti sono stati analizzati con successo.\n\nFile CSV uniti:\n"
                + "\n".join(merged_files),
            )

    def _wrap_layout(self, child_layout: QHBoxLayout) -> QWidget:
        widget = QWidget()
        widget.setLayout(child_layout)
        return widget

    def _select_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona video partita",
            str(Path.cwd()),
            "Video Files (*.mp4 *.avi *.mov *.mkv)",
        )
        if path:
            self.video_input.setText(path)
            self._show_local_video_thumbnail(path)

    def _on_video_input_changed(self) -> None:
        if self.source_type_combo.currentIndex() == 0:
            video_path = self.video_input.text().strip()
            if video_path:
                self._show_local_video_thumbnail(video_path)

    def _show_local_video_thumbnail(self, video_path: str) -> None:
        path = Path(video_path)
        if not path.exists():
            self.preview_label.setText("File video non trovato")
            return
        cap = cv2.VideoCapture(str(path))
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            self.preview_label.setText("Impossibile leggere anteprima video")
            return
        self._set_preview_frame(frame)

    def _play_local_preview_clip(self) -> None:
        if self.source_type_combo.currentIndex() != 0:
            QMessageBox.information(
                self,
                "Anteprima locale",
                "Questa funzione è disponibile solo con sorgente 'File Locale'.",
            )
            return

        video_path = self.video_input.text().strip()
        if not video_path or not Path(video_path).exists():
            QMessageBox.warning(self, "Errore", "Seleziona prima un file video valido")
            return

        self._stop_preview()
        self.preview_cap = cv2.VideoCapture(video_path)
        if not self.preview_cap.isOpened():
            self.preview_label.setText("Impossibile aprire il video per anteprima")
            return

        fps = self.preview_cap.get(cv2.CAP_PROP_FPS)
        if fps is None or fps <= 0:
            fps = 30.0
        self.preview_frames_left = max(1, int(round(fps * 3.0)))
        self.preview_timer.start(33)
        self._append_log("Anteprima locale 3s avviata")

    def _select_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Seleziona cartella output", str(Path.cwd())
        )
        if path:
            self.output_input.setText(path)

    def _detect_field_with_ai(self) -> None:
        if self.source_type_combo.currentIndex() != 0:
            QMessageBox.warning(
                self,
                "Rilevamento AI campo",
                "Per ora il rilevamento AI automatico è disponibile sui file video locali.",
            )
            return

        video_path = self.video_input.text().strip()
        if not video_path or not Path(video_path).exists():
            QMessageBox.warning(
                self, "Errore", "Seleziona prima un video locale valido"
            )
            return

        model_path, _ = QFileDialog.getOpenFileName(
            self,
            "Scegli modello AI campo/keypoints",
            str(Path.cwd()),
            "Modelli PyTorch (*.pt);;Tutti i file (*)",
        )
        if not model_path:
            return

        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            QMessageBox.critical(self, "Errore", "Impossibile leggere il primo frame")
            return

        try:
            from ..core.court_ai import CourtKeypointDetector

            detector = CourtKeypointDetector(model_path)
            points = detector.detect_field_points(frame)
            if not points:
                QMessageBox.warning(
                    self,
                    "Campo non rilevato",
                    "Il modello non ha restituito 4 keypoint. Usa la calibrazione manuale o un modello keypoint addestrato.",
                )
                return
            num_fields = self.config_store.load_num_fields()
            self.config_store.save_field_points(points, num_fields=num_fields)
            self.calibration_label.setText(self._calibration_summary())
            self._append_log(f"Campo rilevato con AI e salvato: {points}")
            QMessageBox.information(
                self, "Campo rilevato", "Calibrazione campo aggiornata tramite AI."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Errore AI campo", str(exc))

    def _open_calibration(self) -> None:
        """Apri la finestra di calibrazione usando il primo frame della sorgente selezionata.

        Supporta file locali, stream IP e webcam.
        """
        source_index = self.source_type_combo.currentIndex()

        frame = None

        # File locale
        if source_index == 0:
            video_path_str = self.video_input.text().strip()
            if not video_path_str:
                QMessageBox.warning(self, "Errore", "Seleziona prima un video valido")
                return
            video_path = Path(video_path_str)
            if not video_path.exists():
                QMessageBox.warning(self, "Errore", "Il file video non esiste")
                return

            cap = cv2.VideoCapture(str(video_path))
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                QMessageBox.critical(
                    self,
                    "Errore",
                    "Impossibile leggere il primo frame dal file selezionato.",
                )
                return

        # Webcam
        elif source_index == 2:
            # Preferisci il frame dal preview se attivo
            if (
                hasattr(self, "preview_cap")
                and self.preview_cap is not None
                and self.preview_cap.isOpened()
            ):
                ret, frame = self.preview_cap.read()
                if not ret or frame is None:
                    frame = None
            else:
                device_id = self.webcam_combo.currentData()
                if device_id is None or device_id == -1:
                    QMessageBox.warning(
                        self, "Errore", "Nessuna webcam valida selezionata"
                    )
                    return
                cap = cv2.VideoCapture(int(device_id))
                ret, frame = cap.read()
                cap.release()
                if not ret or frame is None:
                    QMessageBox.critical(
                        self,
                        "Errore",
                        "Impossibile leggere un frame dalla webcam selezionata.",
                    )
                    return

        # Stream IP
        else:
            url = self.video_input.text().strip()
            if not url:
                QMessageBox.warning(self, "Errore", "Inserisci l'URL dello stream")
                return

            # Imposta opzioni FFmpeg per ridurre latency quando possibile
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;tcp|analyzeduration;500000|probesize;5000000"
            )

            cap = cv2.VideoCapture(url)

            # Prova a leggere alcuni frame (ritenta se necessario)
            ret = False
            frame = None
            for attempt in range(3):
                ret, frame = cap.read()
                if ret and frame is not None:
                    break
                time.sleep(0.7)
            cap.release()

            if not ret or frame is None:
                QMessageBox.critical(
                    self,
                    "Errore",
                    "Impossibile leggere un frame dallo stream. Controlla URL e connessione.",
                )
                return

        # Apri la dialog di calibrazione passando il frame catturato
        dialog = CalibrationDialog(frame, self)
        if dialog.exec():
            self.calibration_label.setText(self._calibration_summary())
            self._append_log("Calibrazione campo aggiornata")

    def _start_analysis(self) -> None:
        # Se è webcam (ID int)
        if self.source_type_combo.currentIndex() == 2:
            device_id = self.webcam_combo.currentData()
            if device_id is None or device_id == -1:
                QMessageBox.warning(self, "Errore", "Nessuna webcam valida selezionata")
                return
            video_source = device_id
        else:
            video_source_text = self.video_input.text().strip()
            if not video_source_text:
                QMessageBox.warning(
                    self, "Errore", "Inserisci una sorgente video valida"
                )
                return

            if self.source_type_combo.currentIndex() == 0:
                # È un file locale
                video_path = Path(video_source_text)
                if not video_path.exists():
                    QMessageBox.warning(
                        self, "Errore", "Il file video selezionato non esiste"
                    )
                    return
                video_source = str(video_path)
            else:
                # È uno stream IP
                video_source = video_source_text

        detector_type = self.detector_combo.currentText()
        use_instance_segmentation = self.segmentation_cb.isChecked()
        detector_model = self._resolve_detector_model(
            self.model_input.text(), use_instance_segmentation
        )
        if use_instance_segmentation:
            detector_type = "yolo"
        if detector_type == "yolo":
            QMessageBox.warning(
                self,
                "Attenzione YOLO",
                "YOLO richiede molta memoria RAM/VRAM.\n"
                "Se l'app si chiude improvvisamente, riprova con HOG.",
            )
        try:
            output_dir = self.output_input.text().strip() or str(
                (Path.cwd() / "output").resolve()
            )
            num_fields = self.config_store.load_num_fields()
            config = PipelineConfig(
                video_path=video_source,
                output_dir=output_dir,
                sample_every_n_frames=self.sample_spin.value(),
                detector_model=detector_model,
                detector_confidence=self.conf_spin.value(),
                field_points=self.config_store.load_field_points(),
                detector_type=detector_type,
                num_fields=num_fields,
                use_hw_accel=self.hw_accel_cb.isChecked(),
                use_instance_segmentation=use_instance_segmentation,
                jersey_classifier_model=self.jersey_classifier_input.text().strip()
                or None,
            )

            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress.setValue(0)
            self.status_label.setText("Analisi in corso...")
            self.log_output.clear()
            self.preview_label.setText("Analisi avviata...")
            self._append_log(f"Configurazione caricata per: {video_source}")
            self._append_log(f"Modello detector in uso: {config.detector_model}")
            self._update_active_model_label(config.detector_model)
            if config.use_instance_segmentation:
                self._append_log(
                    f"Instance segmentation attiva con modello: {config.detector_model}"
                )
            self._append_log(f"Punti campo: {config.field_points}")
            self._append_log(f"Numero campi: {config.num_fields}")
            chunk_seconds = self.chunk_spin.value()
            self.worker = AnalysisWorker(config, chunk_seconds=chunk_seconds)
            self.worker.log_message.connect(self._append_log)
            self.worker.progress_update.connect(self._on_progress)
            self.worker.finished_success.connect(self._on_success)
            self.worker.finished_error.connect(self._on_error)
            # Stop any live preview (webcam) to free the device while analyzing
            try:
                self._stop_preview()
            except Exception:
                pass

            self.worker.start()
        except Exception as e:
            QMessageBox.critical(
                self, "Errore critico", f"Errore durante l'analisi:\n{e}"
            )
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def _on_progress(self, payload: dict) -> None:
        processed = int(payload.get("processed_frames", 0))
        total = max(1, int(payload.get("total_processed_frames", 1)))
        percent = min(100, int(processed / total * 100))
        self.progress.setValue(percent)
        self.status_label.setText(f"Analisi in corso... {percent}%")
        self.frame_label.setText(f"Frame: {payload.get('frame_idx', '-')}")
        self.time_label.setText(f"Tempo: {float(payload.get('timestamp', 0.0)):.1f}s")
        self.detection_label.setText(f"Detection: {payload.get('detections', 0)}")
        self.track_label.setText(f"Track: {payload.get('tracks', 0)}")

        preview = payload.get("preview_frame")
        if preview is not None:
            self._set_preview_frame(preview)

        if processed == 1 or processed % 25 == 0:
            self._append_log(
                f"Progress {percent}% | frame={payload.get('frame_idx')} | det={payload.get('detections')} | track={payload.get('tracks')}"
            )

    def _set_preview_frame(self, frame) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image.copy())
        self.preview_label.setPixmap(
            pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _on_success(self, exported: dict) -> None:
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress.setValue(100)
        self.status_label.setText("Analisi completata")
        self._append_log("File generati:")
        for key, value in exported.items():
            self._append_log(f"- {key}: {value}")
        QMessageBox.information(self, "Completato", "Analisi completata con successo")

    def _on_error(self, message: str) -> None:
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if "interrotta dall'utente" in (message or "").lower():
            self.status_label.setText("Analisi interrotta")
            self._append_log("Analisi interrotta dall'utente")
            QMessageBox.information(
                self, "Interrotta", "Analisi interrotta su richiesta"
            )
            return

        self.progress.setValue(0)
        self.status_label.setText("Errore")
        self._append_log(f"Errore: {message}")
        QMessageBox.critical(self, "Errore", message)

    def _stop_analysis(self) -> None:
        if self.worker is not None:
            self.worker.stop()
            self.status_label.setText("Stop richiesto...")
            self._append_log("Richiesta di stop inviata...")
        self.stop_button.setEnabled(False)

    def _generate_zone_report(self):
        """Genera report dettagliato delle zone occupate con heatmap e PDF."""
        output_dir = self.output_input.text().strip() or str(
            (Path.cwd() / "output").resolve()
        )
        tracks_csv = Path(output_dir) / "tracks.csv"
        if not tracks_csv.exists():
            QMessageBox.warning(
                self,
                "Errore",
                "Nessun file tracks.csv trovato. Esegui prima un'analisi.",
            )
            return

        # Carica i dati
        try:
            import pandas as pd
        except ImportError:
            QMessageBox.critical(
                self,
                "Errore",
                "Pandas non installato. Installa con: pip install pandas",
            )
            return

        df = pd.read_csv(tracks_csv)
        if df.empty:
            QMessageBox.warning(self, "Errore", "Il file tracks.csv è vuoto.")
            return

        # Conteggio giocatori unici
        unique_players = df["track_id"].nunique()

        # Conteggio per squadra
        team_counts = df["team_id"].value_counts()
        team_info = "\nDistribuzione per squadra:\n"
        for team, count in team_counts.items():
            team_info += f"- {team}: {count} campioni\n"

        # Calcola tempo per zona
        zone_times = {}
        zone_player_counts = {}  # Numero di giocatori unici per zona

        for zone in df["zone"].unique():
            zone_data = df[df["zone"] == zone]
            if not zone_data.empty:
                zone_times[zone] = (
                    zone_data["timestamp"].max() - zone_data["timestamp"].min()
                )
                zone_player_counts[zone] = zone_data["track_id"].nunique()

        if not zone_times:
            QMessageBox.warning(self, "Errore", "Nessuna zona trovata nei dati.")
            return

        # Statistiche generali
        total_time = sum(zone_times.values())
        max_zone = max(zone_times, key=zone_times.get)
        min_zone = min(zone_times, key=zone_times.get)
        avg_time = total_time / len(zone_times)

        # Nomi zone pallavolo reali (1-6)
        zone_names = {
            1: "Zona 1 (posto 1 / battuta-difesa destra)",
            2: "Zona 2 (posto 2 / attacco destra)",
            3: "Zona 3 (posto 3 / centrale rete)",
            4: "Zona 4 (posto 4 / attacco sinistra)",
            5: "Zona 5 (posto 5 / difesa sinistra)",
            6: "Zona 6 (posto 6 / difesa centrale)",
        }

        stats_text = f"""=== REPORT ANALISI CAMPO PALLAVOLO ===

RIEPILOGO GENERALE:
- Giocatori totali individuati: {unique_players}
- Tempo totale analizzato: {total_time:.1f} secondi
- Zona più occupata: {zone_names.get(max_zone, f"Zona {max_zone}")} ({zone_times[max_zone]:.1f}s)
- Zona meno occupata: {zone_names.get(min_zone, f"Zona {min_zone}")} ({zone_times[min_zone]:.1f}s)
- Tempo medio per zona: {avg_time:.1f}s
{team_info}
DETAGLI PER ZONA:
"""
        for zone, time in sorted(zone_times.items()):
            percentage = (time / total_time) * 100 if total_time > 0 else 0
            player_count = zone_player_counts.get(zone, 0)
            stats_text += f"\n{zone_names.get(zone, f'Zona {zone}')}:\n"
            stats_text += f"  - Tempo: {time:.1f}s ({percentage:.1f}%)\n"
            stats_text += f"  - Giocatori: {player_count}\n"

        # Genera immagine campo con heatmap - layout 6 zone per lato
        import cv2
        import numpy as np

        field_img = np.full((760, 520, 3), (245, 190, 95), dtype=np.uint8)
        x0, y0 = 80, 50
        cell_w, cell_h = 120, 150
        court_w, court_h = cell_w * 3, cell_h * 4

        cv2.rectangle(field_img, (x0, y0), (x0 + court_w, y0 + court_h), (0, 0, 0), 3)
        cv2.line(
            field_img, (x0, y0 + cell_h), (x0 + court_w, y0 + cell_h), (0, 0, 0), 2
        )
        cv2.line(
            field_img,
            (x0, y0 + cell_h * 2),
            (x0 + court_w, y0 + cell_h * 2),
            (0, 0, 255),
            5,
        )
        cv2.line(
            field_img,
            (x0, y0 + cell_h * 3),
            (x0 + court_w, y0 + cell_h * 3),
            (0, 0, 0),
            2,
        )
        cv2.line(
            field_img, (x0 + cell_w, y0), (x0 + cell_w, y0 + court_h), (60, 60, 60), 1
        )
        cv2.line(
            field_img,
            (x0 + cell_w * 2, y0),
            (x0 + cell_w * 2, y0 + court_h),
            (60, 60, 60),
            1,
        )

        zone_layout = [
            [1, 6, 5],
            [2, 3, 4],
            [4, 3, 2],
            [5, 6, 1],
        ]

        max_time = max(zone_times.values())
        for row, row_zones in enumerate(zone_layout):
            for col, zone in enumerate(row_zones):
                x = x0 + col * cell_w
                y = y0 + row * cell_h
                time = zone_times.get(zone, 0)
                intensity = int(255 * (time / max_time)) if max_time > 0 else 0
                color = (intensity, 80, 255 - intensity)
                cv2.rectangle(
                    field_img,
                    (x + 2, y + 2),
                    (x + cell_w - 2, y + cell_h - 2),
                    color,
                    -1,
                )

                # Scrivi numero zona
                cv2.putText(
                    field_img,
                    f"Z{zone}",
                    (x + 30, y + 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (255, 255, 255),
                    2,
                )
                # Scrivi tempo
                cv2.putText(
                    field_img,
                    f"{time:.1f}s",
                    (x + 20, y + 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    1,
                )
                # Scrivi numero giocatori
                player_count = zone_player_counts.get(zone, 0)
                cv2.putText(
                    field_img,
                    f"{player_count} player(s)",
                    (x + 10, y + 110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1,
                )

        # Aggiungi titolo e legenda
        cv2.putText(
            field_img,
            "HEATMAP - Tempo di Permanenza per Zona",
            (50, 690),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            1,
        )
        cv2.putText(
            field_img,
            "Legenda: Rosso=Poco tempo | Blu=Molto tempo",
            (50, 720),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            1,
        )

        # Salva immagine
        report_path = Path(output_dir) / "zone_report_detailed.png"
        cv2.imwrite(str(report_path), field_img)

        # Salva statistiche in testo
        stats_path = Path(output_dir) / "zone_stats_detailed.txt"
        with open(stats_path, "w", encoding="utf-8") as f:
            f.write(stats_text)

        # Genera PDF
        pdf_msg = ""
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=14, style="B")
            pdf.cell(
                200,
                15,
                txt="Report Dettagliato Zone Campo Pallavolo",
                ln=True,
                align="C",
            )
            pdf.set_font("Arial", size=11)
            pdf.ln(5)
            for line in stats_text.strip().split("\n"):
                pdf.multi_cell(200, 6, txt=line)
            pdf.ln(5)
            # Aggiungi immagine
            pdf.image(str(report_path), x=10, y=pdf.get_y(), w=190)
            pdf_path = Path(output_dir) / "zone_report_detailed.pdf"
            pdf.output(str(pdf_path))
            pdf_msg = f"\n- PDF: {pdf_path}"
        except ImportError:
            pdf_msg = "\n(Installa fpdf per esportare PDF: pip install fpdf)"
        except Exception as e:
            pdf_msg = f"\n(Errore nella generazione PDF: {e})"

        # Mostra messaggio con statistiche
        msg = f"""Report dettagliato delle zone salvato:
- Immagine: {report_path}
- Statistiche: {stats_path}{pdf_msg}

{stats_text}"""
        QMessageBox.information(self, "Report generato", msg)
        self._append_log("Report dettagliato zone generato con successo")

    def _open_report_dialog(self):
        """Apre una dialog per selezionare e aprire i report generati."""
        output_dir = self.output_input.text().strip() or str(
            (Path.cwd() / "output").resolve()
        )
        output_path = Path(output_dir)

        if not output_path.exists():
            QMessageBox.warning(
                self,
                "Errore",
                f"La cartella output non esiste: {output_path}",
            )
            return

        # Cerca i file report
        report_files = {}

        # Cerca file PNG
        png_files = sorted(output_path.glob("*report*.png"))
        for f in png_files:
            report_files[f"Immagine: {f.name}"] = f

        # Cerca file TXT
        txt_files = sorted(output_path.glob("*report*.txt"))
        for f in txt_files:
            report_files[f"Statistiche: {f.name}"] = f

        # Cerca file PDF
        pdf_files = sorted(output_path.glob("*report*.pdf"))
        for f in pdf_files:
            report_files[f"PDF: {f.name}"] = f

        if not report_files:
            QMessageBox.information(
                self,
                "Nessun report trovato",
                f"Non sono stati trovati file report nella cartella:\n{output_path}",
            )
            return

        # Crea una dialog per scegliere il file
        from PyQt6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QVBoxLayout
        from PyQt6.QtWidgets import QPushButton as QB

        dialog = QDialog(self)
        dialog.setWindowTitle("Seleziona report da aprire")
        dialog.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        # Lista dei file
        file_list = QListWidget()
        for name, path in report_files.items():
            item = QListWidgetItem(name)
            item.setData(256, str(path))  # Salva il path nei dati dell'item
            file_list.addItem(item)

        layout.addWidget(file_list)

        # Pulsanti
        button_layout = QHBoxLayout()

        open_btn = QB("Apri")
        open_btn.clicked.connect(lambda: self._open_selected_report(file_list, dialog))
        button_layout.addWidget(open_btn)

        cancel_btn = QB("Annulla")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        # Pre-seleziona il primo item
        if file_list.count() > 0:
            file_list.setCurrentRow(0)

        dialog.exec()

    def _open_selected_report(self, file_list, dialog):
        """Apre il file report selezionato."""
        current_item = file_list.currentItem()
        if current_item is None:
            QMessageBox.warning(self, "Errore", "Seleziona un file da aprire")
            return

        file_path = current_item.data(256)
        if not file_path:
            QMessageBox.warning(self, "Errore", "Percorso file non valido")
            return

        # Apri il file con l'applicazione di sistema predefinita
        try:
            from open import open as open_file
        except ImportError:
            # Fallback: usa il metodo open del modulo corrente
            try:
                import platform

                system = platform.system()
                if system == "Windows":
                    import subprocess

                    subprocess.Popen(["start", file_path], shell=True)
                elif system == "Darwin":  # macOS
                    import subprocess

                    subprocess.Popen(["open", file_path])
                else:  # Linux
                    import subprocess

                    subprocess.Popen(["xdg-open", file_path])
                self._append_log(f"Apertura file: {Path(file_path).name}")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Errore",
                    f"Impossibile aprire il file:\n{e}",
                )
                return

    def _append_log(self, message: str) -> None:
        self.log_output.appendPlainText(message)

    def _calibration_summary(self) -> str:
        points = self.config_store.load_field_points()
        return " | ".join(f"({int(x)}, {int(y)})" for x, y in points)


def run() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

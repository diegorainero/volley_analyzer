from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFrame,
)


class StatusIndicator(QWidget):
    def __init__(self, label: str, color: str = "#22C55E", parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self.setFixedSize(12, 12)

    def set_color(self, color: str):
        self._color = color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(r)
        p.end()


class CommandBar(QFrame):
    code_submitted = pyqtSignal(str)
    action_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(44)
        self.setStyleSheet("""
            CommandBar {
                background-color: #1F1814;
                border-top: 1px solid #4A382E;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        # Status indicators
        status_layout = QHBoxLayout()
        status_layout.setSpacing(4)

        self.status_db = StatusIndicator("DB", "#22C55E")
        status_layout.addWidget(self.status_db)
        db_label = QLabel("DB")
        db_label.setStyleSheet("color: #9D8878; font-size: 9px; font-weight: bold;")
        status_layout.addWidget(db_label)

        self.status_video = StatusIndicator("VID", "#F97316")
        status_layout.addWidget(self.status_video)
        vid_label = QLabel("Video")
        vid_label.setStyleSheet("color: #9D8878; font-size: 9px; font-weight: bold;")
        status_layout.addWidget(vid_label)

        layout.addLayout(status_layout)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #4A382E;")
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        # Code input
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Codice DataVolley...")
        self.code_input.setClearButtonEnabled(True)
        self.code_input.setFixedHeight(28)
        self.code_input.setStyleSheet("""
            QLineEdit {
                background-color: #3A2D27;
                color: #F6EFE9;
                border: 1px solid #6E4B32;
                border-radius: 4px;
                padding: 2px 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #1D6CFF;
            }
        """)
        self.code_input.returnPressed.connect(self._on_code_submit)
        layout.addWidget(self.code_input, 1)

        # Action buttons
        self.btn_undo = self._make_action_btn("Undo")
        layout.addWidget(self.btn_undo)

        self.btn_redo = self._make_action_btn("Redo")
        layout.addWidget(self.btn_redo)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #4A382E;")
        sep2.setFixedWidth(1)
        layout.addWidget(sep2)

        self.btn_pt = QPushButton("Pt")
        self.btn_pt.setFixedSize(36, 28)
        self.btn_pt.setStyleSheet("""
            QPushButton {
                background-color: #1D6CFF;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2B7AFF;
            }
            QPushButton:pressed {
                background-color: #1557D4;
            }
        """)
        layout.addWidget(self.btn_pt)

        # Status message
        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: #9D8878; font-size: 10px;")
        layout.addWidget(self.status_label)

    def _make_action_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(50, 28)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3A2D27;
                color: #D9CFC5;
                border: 1px solid #5A4A3E;
                border-radius: 4px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4A3A30;
                color: #F6EFE9;
            }
            QPushButton:pressed {
                background-color: #2B211C;
            }
        """)
        btn.clicked.connect(lambda: self.action_requested.emit(text.lower()))
        return btn

    def _on_code_submit(self):
        code = self.code_input.text().strip()
        if code:
            self.code_submitted.emit(code)
            self.code_input.clear()

    def set_status(self, text: str, color: str = "#9D8878"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 10px;")

    def set_db_status(self, ok: bool):
        self.status_db.set_color("#22C55E" if ok else "#EF4444")

    def set_video_status(self, ok: bool):
        self.status_video.set_color("#22C55E" if ok else "#F97316")

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QFontDatabase
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFrame,
)


def _make_font(size: int = 10, bold: bool = False, family: str = "Segoe UI") -> QFont:
    f = QFont(family, size)
    f.setBold(bold)
    return f


class ScorePanel(QWidget):
    def __init__(self, label: str, color: str = "#1D6CFF", parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self._score = 0
        self.setFixedSize(80, 60)

    def set_score(self, value: int):
        self._score = value
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self.rect().adjusted(2, 2, -2, -2)

        # Background
        p.setBrush(QBrush(QColor("#1F1814")))
        p.setPen(QPen(QColor("#4A382E"), 1))
        p.drawRoundedRect(r, 6, 6)

        # Score
        f = QFont("Segoe UI", 28, QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(QColor("#F6EFE9"))
        p.drawText(r.adjusted(0, -6, 0, 0),
                   Qt.AlignmentFlag.AlignCenter, str(self._score))

        # Label
        f2 = QFont("Segoe UI", 7, QFont.Weight.Bold)
        p.setFont(f2)
        p.setPen(QColor("#9D8878"))
        p.drawText(r.adjusted(0, 38, 0, 0),
                   Qt.AlignmentFlag.AlignCenter, self._label)


class ScoreButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(24, 24)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3A2D27;
                color: #F6EFE9;
                border: 1px solid #5A4A3E;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #4A3A30;
                border-color: #1D6CFF;
            }
            QPushButton:pressed {
                background-color: #2B211C;
            }
        """)


class ModernHeader(QFrame):
    pt_home = pyqtSignal()
    pt_away = pyqtSignal()
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(80)
        self.setStyleSheet("""
            ModernHeader {
                background-color: #1F1814;
                border-bottom: 1px solid #4A382E;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(12)

        # Home team
        home_layout = QVBoxLayout()
        home_layout.setSpacing(2)

        self.home_name = QLabel("Casa")
        self.home_name.setFont(_make_font(11, True))
        self.home_name.setStyleSheet("color: #F6EFE9;")
        home_layout.addWidget(self.home_name)

        home_score_row = QHBoxLayout()
        home_score_row.setSpacing(4)
        self.home_score_minus = ScoreButton("-")
        self.home_score_minus.clicked.connect(
            lambda: self._adjust_score("home", -1)
        )
        home_score_row.addWidget(self.home_score_minus)

        self.home_score_panel = ScorePanel("CASA", "#1D6CFF")
        home_score_row.addWidget(self.home_score_panel)

        self.home_score_plus = ScoreButton("+")
        self.home_score_plus.clicked.connect(lambda: self.pt_home.emit())
        home_score_row.addWidget(self.home_score_plus)

        home_layout.addLayout(home_score_row)
        layout.addLayout(home_layout)

        # Center: set info and match state
        center_layout = QVBoxLayout()
        center_layout.setSpacing(2)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.set_label = QLabel("SET 1")
        self.set_label.setFont(_make_font(10, True))
        self.set_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_label.setStyleSheet("color: #1D6CFF;")
        center_layout.addWidget(self.set_label)

        self.match_info = QLabel("Partita #?")
        self.match_info.setFont(_make_font(8))
        self.match_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_info.setStyleSheet("color: #9D8878;")
        center_layout.addWidget(self.match_info)

        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(_make_font(16, True, "Courier New"))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #22C55E;")
        center_layout.addWidget(self.timer_label)

        layout.addLayout(center_layout, 1)

        # Away team
        away_layout = QVBoxLayout()
        away_layout.setSpacing(2)
        away_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.away_name = QLabel("Trasferta")
        self.away_name.setFont(_make_font(11, True))
        self.away_name.setStyleSheet("color: #F6EFE9;")
        self.away_name.setAlignment(Qt.AlignmentFlag.AlignRight)
        away_layout.addWidget(self.away_name)

        away_score_row = QHBoxLayout()
        away_score_row.setSpacing(4)
        away_score_row.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.away_score_minus = ScoreButton("-")
        self.away_score_minus.clicked.connect(
            lambda: self._adjust_score("away", -1)
        )
        away_score_row.addWidget(self.away_score_minus)

        self.away_score_panel = ScorePanel("OSPITI", "#6B7280")
        away_score_row.addWidget(self.away_score_panel)

        self.away_score_plus = ScoreButton("+")
        self.away_score_plus.clicked.connect(lambda: self.pt_away.emit())
        away_score_row.addWidget(self.away_score_plus)

        away_layout.addLayout(away_score_row)
        layout.addLayout(away_layout)

        # Info badges
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.rotation_label = QLabel("Rot. 1")
        self.rotation_label.setFont(_make_font(8))
        self.rotation_label.setStyleSheet(
            "color: #D9CFC5; background-color: #3A2D27;"
            "border: 1px solid #5A4A3E; border-radius: 4px; padding: 2px 8px;"
        )
        info_layout.addWidget(self.rotation_label)

        self.timeout_label = QLabel("TO: 0/2")
        self.timeout_label.setFont(_make_font(8))
        self.timeout_label.setStyleSheet(
            "color: #F97316; background-color: #3A2D27;"
            "border: 1px solid #5A4A3E; border-radius: 4px; padding: 2px 8px;"
        )
        info_layout.addWidget(self.timeout_label)

        layout.addLayout(info_layout)

    def _adjust_score(self, side: str, delta: int):
        if side == "home":
            current = int(self.home_score_panel._score)
            new = max(0, current + delta)
            self.home_score_panel.set_score(new)
        else:
            current = int(self.away_score_panel._score)
            new = max(0, current + delta)
            self.away_score_panel.set_score(new)

    def set_scores(self, home: int, away: int):
        self.home_score_panel.set_score(home)
        self.away_score_panel.set_score(away)

    def set_team_names(self, home: str, away: str):
        self.home_name.setText(home)
        self.away_name.setText(away)

    def set_set_number(self, n: int):
        self.set_label.setText(f"SET {n}")

    def set_timer(self, text: str):
        self.timer_label.setText(text)

    def set_rotation(self, n: int | None):
        self.rotation_label.setText(f"Rot. {n or 1}")

    def set_timeout(self, used: int, limit: int = 2):
        self.timeout_label.setText(f"TO: {used}/{limit}")

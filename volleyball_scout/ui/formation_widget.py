from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPainterPath
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFrame,
)

POS_TO_ZONE = {"P1": "1", "P2": "2", "P3": "3", "P4": "4", "P5": "5", "P6": "6"}
VISUAL_GRID_HOME = (("P5", "P4"), ("P6", "P3"), ("P1", "P2"))
VISUAL_GRID_AWAY = (("P2", "P1"), ("P3", "P6"), ("P4", "P5"))


class PlayerCell(QFrame):
    def __init__(self, pos_code: str, parent=None):
        super().__init__(parent)
        self._pos_code = pos_code
        self._player_number: str = "-"
        self._highlighted = False
        self._is_libero = False
        self._setter_number: str | None = None
        self.setMinimumSize(96, 80)
        self.setStyleSheet("QFrame { border: none; background: transparent; }")

    def set_player(self, number: str, highlighted=False, is_libero=False, setter=None):
        self._player_number = number
        self._highlighted = highlighted
        self._is_libero = is_libero
        self._setter_number = setter
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        cx, cy = r.center().x(), r.center().y()
        radius = min(r.width(), r.height()) * 0.32

        if self._is_libero:
            bg = QColor("#F59E0B")
            border = QPen(QColor("#D97706"), 2)
        elif self._highlighted:
            bg = QColor("#DC2626")
            border = QPen(QColor("#7F1D1D"), 2)
        else:
            bg = QColor("#E5E7EB")
            border = QPen(QColor("#CBD5E1"), 1)

        p.setPen(border)
        p.setBrush(bg)
        p.drawEllipse(QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius))

        display = self._player_number
        if self._setter_number and self._player_number == self._setter_number:
            display = f"{self._player_number}P"

        p.setPen(QColor("#111827") if not self._is_libero else QColor("#FFFFFF"))
        f = QFont()
        f.setPointSize(int(radius * 0.55))
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius),
                    Qt.AlignmentFlag.AlignCenter, display)
        p.end()


class HalfCourtWidget(QWidget):
    def __init__(self, team_side: str, team_name: str = "", parent=None):
        super().__init__(parent)
        self._team_side = team_side
        self._team_name = team_name
        self._cells: dict[str, PlayerCell] = {}
        self._highlight_number: str | None = None
        self._libero_number: str | None = None
        self._setter_number: str | None = None
        self._setup_ui()

    def _grid(self):
        return VISUAL_GRID_AWAY if self._team_side == "away" else VISUAL_GRID_HOME

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.setStyleSheet("""
            HalfCourtWidget {
                border: 1px solid #B79C8A;
                border-radius: 10px;
                background-color: #2F241F;
            }
        """)

        left_margin = 8 if self._team_side == "home" else 40
        right_margin = 40 if self._team_side == "home" else 8
        inner = QVBoxLayout()
        inner.setContentsMargins(left_margin, 40, right_margin, 40)
        inner.setSpacing(0)

        court_frame = QFrame()
        court_frame.setStyleSheet(
            "QFrame { background-color: #5D8CD8; border-radius: 6px; }"
        )
        court_layout = QVBoxLayout(court_frame)
        court_layout.setContentsMargins(10, 10, 10, 10)

        grid = QGridLayout()
        grid.setSpacing(10)

        for row, row_positions in enumerate(self._grid()):
            for col, pos_code in enumerate(row_positions):
                cell = PlayerCell(pos_code)
                cell.setMinimumSize(96, 80)
                self._cells[pos_code] = cell
                grid.addWidget(cell, row, col)

        court_layout.addLayout(grid)
        inner.addWidget(court_frame)
        outer.addLayout(inner)

    def update_lineup(self, lineup: dict[str, str] | None):
        if lineup is None:
            lineup = {}
        for pos_code, cell in self._cells.items():
            raw = lineup.get(pos_code, "-")
            num = raw.strip()
            if not num or num == "-":
                cell.set_player("-", setter=self._setter_number)
                continue
            is_libero = self._libero_number is not None and num == self._libero_number
            highlighted = self._highlight_number is not None and num == self._highlight_number
            cell.set_player(num, highlighted=highlighted, is_libero=is_libero,
                            setter=self._setter_number)

    def set_libero(self, libero_number: str | None):
        self._libero_number = libero_number

    def set_setter(self, setter_number: str | None):
        self._setter_number = setter_number

    def highlight_player(self, player_number: str | None):
        self._highlight_number = player_number

    def clear_highlights(self):
        self._highlight_number = None

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return QSize(280, 200)


class FormationWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._home_libero: str | None = None
        self._away_libero: str | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Sestetto e Rotazioni")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Rotazione:"))
        self._rotation_combo = QComboBox()
        self._rotation_combo.addItems([str(i) for i in range(1, 7)])
        self._rotation_combo.currentIndexChanged.connect(self._on_rotation_changed)
        controls.addWidget(self._rotation_combo)
        controls.addStretch()
        layout.addLayout(controls)

        courts = QHBoxLayout()

        self._home_court = HalfCourtWidget("home", "CASA")
        courts.addWidget(self._home_court, 1)

        center = QVBoxLayout()
        center.addStretch()
        net_label = QLabel("┃ RETE ┃")
        net_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        net_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff; padding: 10px;")
        center.addWidget(net_label)
        center.addStretch()
        courts.addLayout(center)

        self._away_court = HalfCourtWidget("away", "TRASFERTA")
        courts.addWidget(self._away_court, 1)

        layout.addLayout(courts)
        self._rot = 1

    def update_lineups(self, home_lineup: dict[str, str] | None,
                        away_lineup: dict[str, str] | None,
                        rotation: int = 1):
        if home_lineup is None:
            home_lineup = {f"P{i}": "-" for i in range(1, 7)}
        if away_lineup is None:
            away_lineup = {f"P{i}": "-" for i in range(1, 7)}

        rot = max(1, min(6, rotation))
        if self._rotation_combo.currentIndex() + 1 != rot:
            self._rotation_combo.blockSignals(True)
            self._rotation_combo.setCurrentIndex(rot - 1)
            self._rotation_combo.blockSignals(False)

        self._home_court.update_lineup(home_lineup)
        self._away_court.update_lineup(away_lineup)
        self._rot = rot

    def set_libero(self, home_libero: str | None, away_libero: str | None):
        self._home_libero = home_libero
        self._away_libero = away_libero
        self._home_court.set_libero(home_libero)
        self._away_court.set_libero(away_libero)

    def set_setter(self, home_setter: str | None, away_setter: str | None):
        self._home_court.set_setter(home_setter)
        self._away_court.set_setter(away_setter)

    def _on_rotation_changed(self, index: int):
        pass

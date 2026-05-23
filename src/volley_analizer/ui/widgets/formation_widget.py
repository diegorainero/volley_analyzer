from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF, QSize, QPointF
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPainterPath
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QSizePolicy


ROTATION_ZONE_LABELS = {
    1: "Z1", 2: "Z2", 3: "Z3",
    4: "Z4", 5: "Z5", 6: "Z6",
}

ZONE_ORDER = [4, 3, 2, 5, 6, 1]


class CourtWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        home_color: str = "#2196F3",
        away_color: str = "#F44336",
    ):
        super().__init__(parent)
        self._lineup: dict[str, str] = {f"P{i}": "-" for i in range(1, 7)}
        self._rotation = 1
        self._team_side = "home"
        self._home_color = QColor(home_color)
        self._away_color = QColor(away_color)
        self._player_names: dict[str, str] = {}
        self.setMinimumSize(250, 350)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_lineup(self, lineup: dict[str, str], rotation: int = 1):
        self._lineup = dict(lineup) if lineup else {f"P{i}": "-" for i in range(1, 7)}
        self._rotation = max(1, min(6, rotation))
        self.update()

    def set_player_names(self, names: dict[str, str]):
        self._player_names = dict(names)
        self.update()

    def set_team_side(self, side: str):
        self._team_side = side
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        margin = 20
        usable_w = w - 2 * margin
        usable_h = h - 2 * margin
        cell_w = usable_w / 3
        cell_h = usable_h / 2
        center_x = w / 2
        center_y = h / 2

        self._draw_court(painter, w, h, margin, cell_w, cell_h)
        self._draw_net(painter, w, margin, center_y)
        self._draw_players(painter, margin, margin, cell_w, cell_h, center_y)
        self._draw_rotation_label(painter, w, h)

    def _draw_court(self, painter: QPainter, w: int, h: int,
                     margin: int, cell_w: float, cell_h: float):
        painter.setPen(QPen(QColor("#333333"), 2))
        painter.setBrush(QBrush(QColor("#1a1a2e")))

        path = QPainterPath()
        path.addRoundedRect(QRectF(margin, margin, w - 2 * margin, h - 2 * margin), 8, 8)
        painter.drawPath(path)

        painter.setPen(QPen(QColor("#444444"), 1, Qt.PenStyle.DashLine))
        center_y = h / 2
        painter.drawLine(int(margin), int(center_y), int(w - margin), int(center_y))

        for col in range(1, 3):
            x = margin + col * cell_w
            painter.drawLine(int(x), int(margin + cell_h),
                             int(x), int(h - margin))

    def _draw_net(self, painter: QPainter, w: int, margin: int, center_y: float):
        painter.setPen(QPen(QColor("#ffffff"), 3))
        net_top = int(center_y - 10)
        net_bottom = int(center_y + 10)
        painter.drawLine(int(margin), net_top, int(w - margin), net_top)
        painter.drawLine(int(margin), net_bottom, int(w - margin), net_bottom)

        painter.setPen(QPen(QColor("#888888"), 1))
        dash_count = 8
        for i in range(1, dash_count):
            x = margin + (w - 2 * margin) * i / dash_count
            painter.drawLine(int(x), net_top, int(x), net_bottom)

        painter.setPen(QColor("#ffffff"))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(QRectF(int(margin), int(net_top - 18),
                                 int(w - 2 * margin), 16),
                         Qt.AlignmentFlag.AlignCenter, "RETE")

    def _draw_players(self, painter: QPainter, margin_x: int, margin_y: int,
                       cell_w: float, cell_h: float, center_y: float):
        player_color = self._home_color if self._team_side == "home" else self._away_color

        for zone_idx, zone in enumerate(ZONE_ORDER):
            row = zone_idx // 3
            col = zone_idx % 3

            cx = margin_x + col * cell_w + cell_w / 2
            cy = margin_y + row * cell_h + cell_h / 2

            if self._team_side == "home":
                cy = margin_y + (1 - row) * cell_h + cell_h / 2

            radius = min(cell_w, cell_h) * 0.25

            painter.setPen(QPen(player_color.darker(150), 2))
            painter.setBrush(QBrush(player_color))

            painter.drawEllipse(QPointF(cx, cy), radius, radius)

            pos_key = f"P{zone}"
            player_num = self._lineup.get(pos_key, "-")

            painter.setPen(QColor("#ffffff"))
            font = QFont()
            font.setPointSize(int(radius * 0.7))
            font.setBold(True)
            painter.setFont(font)

            painter.drawText(QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius),
                             Qt.AlignmentFlag.AlignCenter, str(player_num))

            font_small = QFont()
            font_small.setPointSize(int(radius * 0.35))
            painter.setFont(font_small)
            painter.setPen(QColor("#aaaaaa"))
            zone_label = ROTATION_ZONE_LABELS.get(zone, f"Z{zone}")
            painter.drawText(QRectF(cx - radius, cy + radius - 4, 2 * radius, 12),
                             Qt.AlignmentFlag.AlignCenter, zone_label)

    def _draw_rotation_label(self, painter: QPainter, w: int, h: int):
        painter.setPen(QColor("#ffffff"))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(5, 5, 100, 20),
                         Qt.AlignmentFlag.AlignLeft,
                         f"Rotazione: {self._rotation}")

        team_label = "CASA" if self._team_side == "home" else "TRASFERTA"
        painter.drawText(QRectF(w - 105, 5, 100, 20),
                         Qt.AlignmentFlag.AlignRight,
                         team_label)


class FormationWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self._rot = 1

        title = QLabel("Sestetto")
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

        court_layout = QHBoxLayout()

        self._home_court = CourtWidget(home_color="#2196F3")
        self._home_court.set_team_side("home")
        court_layout.addWidget(self._home_court)

        self._away_court = CourtWidget(away_color="#F44336")
        self._away_court.set_team_side("away")
        court_layout.addWidget(self._away_court)

        layout.addLayout(court_layout)

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

        self._home_court.set_lineup(home_lineup, rot)
        self._away_court.set_lineup(away_lineup, rot)
        self._rot = rot

    def _on_rotation_changed(self, index: int):
        rot = index + 1
        self._home_court.set_lineup(self._home_court._lineup, rot)
        self._away_court.set_lineup(self._away_court._lineup, rot)

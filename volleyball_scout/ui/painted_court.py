from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QSizePolicy,
    QWidget,
)

# Old TeamCourtWidget visual grids — maps (row, col) to position code
# Row 0 = top (left sideline area), Row 2 = bottom (right sideline area)
# Col 0 = back of court, Col 1 = front (net side)
VISUAL_GRID_HOME = (("P5", "P4"), ("P6", "P3"), ("P1", "P2"))
# Col 0 = front (net side), Col 1 = back of court
VISUAL_GRID_AWAY = (("P2", "P1"), ("P3", "P6"), ("P4", "P5"))

# Normalized (x, y) center for each position in the 3×2 grid (home).
# x: 0=back, 1=front(net side) — y: 0=left-sideline, 1=right-sideline
_HOME_POSITIONS: dict[str, tuple[float, float]] = {
    "P1": (0.25, 0.83),  # back, right-sideline  ← VISUAL_GRID_HOME row 2 col 0
    "P2": (0.75, 0.83),  # front, right-sideline ← VISUAL_GRID_HOME row 2 col 1
    "P3": (0.75, 0.50),  # front, center         ← VISUAL_GRID_HOME row 1 col 1
    "P4": (0.75, 0.17),  # front, left-sideline  ← VISUAL_GRID_HOME row 0 col 1
    "P5": (0.25, 0.17),  # back, left-sideline   ← VISUAL_GRID_HOME row 0 col 0
    "P6": (0.25, 0.50),  # back, center          ← VISUAL_GRID_HOME row 1 col 0
}

_AWAY_POSITIONS: dict[str, tuple[float, float]] = {
    "P1": (0.75, 0.17),  # back, left-sideline  ← VISUAL_GRID_AWAY row 0 col 1
    "P2": (0.25, 0.17),  # front, left-sideline ← VISUAL_GRID_AWAY row 0 col 0
    "P3": (0.25, 0.50),  # front, center        ← VISUAL_GRID_AWAY row 1 col 0
    "P4": (0.25, 0.83),  # front, right-sideline← VISUAL_GRID_AWAY row 2 col 0
    "P5": (0.75, 0.83),  # back, right-sideline ← VISUAL_GRID_AWAY row 2 col 1
    "P6": (0.75, 0.50),  # back, center         ← VISUAL_GRID_AWAY row 1 col 1
}

POSITION_ORDER = ["P5", "P4", "P6", "P3", "P1", "P2"]


class _DragLabel(QLabel):
    def __init__(self, text: str, color: str = "#F59E0B", parent=None):
        super().__init__(parent)
        self._drag_color = color
        self.setText(text)
        self.setFixedSize(40, 40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.setFont(f)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: #FFFFFF;
                border: 2px solid #D97706;
                border-radius: 20px;
                font-weight: bold;
            }}
        """)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        parent = self.parent()
        if parent and hasattr(parent, '_handle_libero_drop'):
            parent._handle_libero_drop(self, event.globalPosition().toPoint())


class PaintedCourt(QWidget):
    cellClicked = pyqtSignal(str, str, str, float, float)
    liberoDropped = pyqtSignal(str, str, str, str)
    liberoRevertRequested = pyqtSignal(str)

    def __init__(self, side: str = "home", parent=None):
        super().__init__(parent)
        self._side = side
        self._lineup: dict[str, str] = {}
        self._libero_number: str | None = None
        self._highlight_number: str | None = None
        self._setter_number: str | None = None
        self._hover_pos: str | None = None
        self._serving = False
        self._clickable = False
        self._reception_positions: dict[str, tuple[float, float]] | None = None
        self._active_player: str | None = None

        self._drag_label: _DragLabel | None = None
        self._replaced_label: QLabel | None = None
        self._flash_pos: str | None = None

        self.setMinimumSize(140, 160)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.setMouseTracking(True)

    # ---- Public API ----

    def update_lineup(
        self,
        team_name: str,
        positions: dict,
        libero=None,
        replaced_player: str | None = None,
        serving=False,
        setter_number: str | None = None,
    ):
        self._lineup = dict(positions or {})
        self._libero_number = self._clean(libero)
        self._serving = serving
        self._setter_number = self._clean(setter_number)
        self._active_player = self._clean(replaced_player)
        self._update_libero_label()
        self._update_replaced_label(replaced_player)
        self.update()

    def set_highlight_player(self, number: str | None):
        self._highlight_number = self._clean(number)
        self.update()

    def clear_highlight(self):
        self._highlight_number = None
        self.update()

    def flash_position(self, pos_code: str):
        self._flash_pos = pos_code
        self.update()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, self._clear_flash)

    def _clear_flash(self):
        self._flash_pos = None
        self.update()

    def setClickable(self, clickable: bool):
        self.set_clickable(clickable)

    def set_clickable(self, clickable: bool):
        self._clickable = clickable
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if clickable else Qt.CursorShape.ArrowCursor
        )
        self.update()

    def set_reception_positions(self, positions: dict | None):
        self._reception_positions = positions
        self.update()

    def set_libero_number(self, number: str | None):
        self._libero_number = self._clean(number)
        self._update_libero_label()

    def get_cell_center(self, pos_code: str) -> QPointF | None:
        return self._cell_center(pos_code)

    def clear_highlights(self):
        self.clear_highlight()

    # ---- Internal helpers ----

    @staticmethod
    def _clean(val) -> str | None:
        if val is None:
            return None
        s = str(val).strip()
        return s if s and s not in ("-", "", "None") else None

    def _zone_for_pos(self, pos_code: str) -> str:
        return pos_code.replace("P", "")

    def _draw_rect(self) -> QRectF:
        m = 4
        return QRectF(m, m, self.width() - 2 * m, self.height() - 2 * m)

    def _cell_center(self, pos_code: str) -> QPointF | None:
        grid = _HOME_POSITIONS if self._side == "home" else _AWAY_POSITIONS
        if pos_code not in grid:
            return None
        nx, ny = grid[pos_code]
        dr = self._draw_rect()
        return QPointF(dr.x() + nx * dr.width(), dr.y() + ny * dr.height())

    def _find_pos_at(self, pos: QPointF) -> str | None:
        for pos_code in POSITION_ORDER:
            center = self._cell_center(pos_code)
            if center is None:
                continue
            dx = pos.x() - center.x()
            dy = pos.y() - center.y()
            if dx * dx + dy * dy <= 22 * 22:
                return pos_code
        return None

    def _find_pos_code_for_player(self, number: str) -> str | None:
        for pos_code, num in self._lineup.items():
            if self._clean(num) == number:
                return pos_code
        return None

    # ---- Libero drag support ----

    def _update_libero_label(self):
        if self._libero_number:
            if self._drag_label is None:
                self._drag_label = _DragLabel(self._libero_number, parent=self)
                self._drag_label.show()
            else:
                self._drag_label.setText(self._libero_number)
            pos_code = self._find_pos_code_for_player(self._libero_number)
            if pos_code:
                center = self._cell_center(pos_code)
                if center:
                    self._drag_label.move(
                        int(center.x() - 20), int(center.y() - 20)
                    )
        else:
            if self._drag_label:
                self._drag_label.hide()

    def _update_replaced_label(self, replaced_player: str | None):
        rp = self._clean(replaced_player)
        if rp:
            if self._replaced_label is None:
                self._replaced_label = QLabel(self)
                self._replaced_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._replaced_label.setStyleSheet("""
                    QLabel {
                        background-color: #374151;
                        color: #F97316;
                        border: 1px solid #F97316;
                        border-radius: 4px;
                        padding: 2px 6px;
                        font-size: 9px;
                        font-weight: bold;
                    }
                """)
                self._replaced_label.show()
            self._replaced_label.setText(f"#{rp}")
            self._replaced_label.adjustSize()
            self._replaced_label.move(self.width() - self._replaced_label.width() - 8, 8)
        else:
            if self._replaced_label:
                self._replaced_label.hide()

    def _handle_libero_drop(self, label: _DragLabel, global_pos):
        local = self.mapFromGlobal(global_pos)
        pos_code = self._find_pos_at(QPointF(local))
        if pos_code and self._libero_number:
            player_num = self._clean(self._lineup.get(pos_code))
            if player_num and player_num != self._libero_number:
                self.liberoDropped.emit(self._side, pos_code, player_num, self._libero_number)

    def mouseDoubleClickEvent(self, event):
        if self._active_player:
            self.liberoRevertRequested.emit(self._active_player)
        super().mouseDoubleClickEvent(event)

    # ---- Event handling ----

    def mousePressEvent(self, event):
        if not self._clickable:
            super().mousePressEvent(event)
            return
        pos = event.position()
        pos_code = self._find_pos_at(pos)
        if pos_code:
            zone = self._zone_for_pos(pos_code)
            self.cellClicked.emit(self._side, pos_code, zone, float(pos.x()), float(pos.y()))
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._clickable:
            super().mouseMoveEvent(event)
            return
        pos = event.position()
        found = self._find_pos_at(pos)
        if found != self._hover_pos:
            self._hover_pos = found
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hover_pos is not None:
            self._hover_pos = None
            self.update()
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_libero_label()
        if self._replaced_label:
            self._replaced_label.move(
                self.width() - self._replaced_label.width() - 8, 8
            )

    # ---- Painting ----

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_background(p)

        if self._reception_positions:
            self._draw_reception(p)
        else:
            self._draw_positions(p)

        if self._serving:
            self._draw_serve_indicator(p)

        p.end()

    def _draw_background(self, p: QPainter):
        dr = self._draw_rect()
        p.setBrush(QBrush(QColor("#2F241F")))
        p.setPen(QPen(QColor("#B79C8A"), 1))
        p.drawRoundedRect(dr, 10, 10)

    def _draw_positions(self, p: QPainter):
        for pos_code in POSITION_ORDER:
            center = self._cell_center(pos_code)
            if center is None:
                continue

            player_num = self._clean(self._lineup.get(pos_code))
            is_libero = (
                player_num is not None
                and self._libero_number is not None
                and player_num == self._libero_number
            )
            is_highlighted = (
                player_num is not None
                and self._highlight_number is not None
                and player_num == self._highlight_number
            )
            is_setter = (
                player_num is not None
                and self._setter_number is not None
                and player_num == self._setter_number
            )

            radius = 18

            if is_libero:
                bg = QColor("#F59E0B")
                border = QPen(QColor("#D97706"), 2)
            elif is_highlighted:
                bg = QColor("#DC2626")
                border = QPen(QColor("#7F1D1D"), 2)
            elif self._clickable and pos_code == self._hover_pos:
                bg = QColor("#4B5563")
                border = QPen(QColor("#6B7280"), 2)
            else:
                bg = QColor("#1F2937")
                border = QPen(QColor("#374151"), 2)

            is_flash = pos_code == self._flash_pos

            if is_setter and not is_libero:
                border = QPen(QColor("#1D6CFF"), 2)

            p.setBrush(QBrush(bg))
            p.setPen(border)
            p.drawEllipse(center, radius, radius)

            if is_flash:
                p.setPen(QPen(QColor("#22C55E"), 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(center, radius + 3, radius + 3)

            display = player_num or "-"
            if is_setter and player_num:
                display = f"{player_num}P"

            f = QFont("Segoe UI", 9, QFont.Weight.Bold)
            p.setFont(f)
            p.setPen(QColor("#F6EFE9"))
            p.drawText(
                QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
                Qt.AlignmentFlag.AlignCenter,
                display,
            )

            zone = self._zone_for_pos(pos_code)
            f_small = QFont("Segoe UI", 5)
            p.setFont(f_small)
            p.setPen(QColor("#B0C4DE"))
            p.drawText(
                QRectF(center.x() - 16, center.y() + radius + 8, 32, 10),
                Qt.AlignmentFlag.AlignCenter,
                f"Z{zone}",
            )

    def _draw_reception(self, p: QPainter):
        for pos_code in POSITION_ORDER:
            center = self._cell_center(pos_code)
            if center is None:
                continue

            player_num = self._clean(self._lineup.get(pos_code))

            radius = 14
            bg = QColor("#2D1B69")
            border = QPen(QColor("#6D4FCF"), 2)

            p.setBrush(QBrush(bg))
            p.setPen(border)
            p.drawEllipse(center, radius, radius)

            display = player_num or "-"
            f = QFont("Segoe UI", 7, QFont.Weight.Bold)
            p.setFont(f)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(
                QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
                Qt.AlignmentFlag.AlignCenter,
                display,
            )

    def _draw_serve_indicator(self, p: QPainter):
        p1_center = self._cell_center("P1")
        if p1_center is None:
            return
        p.setBrush(QBrush(QColor("#EF4444")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(p1_center.x(), p1_center.y() - 26), 6, 6)
        f = QFont("Segoe UI", 6, QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(
            QRectF(p1_center.x() - 6, p1_center.y() - 32, 12, 12),
            Qt.AlignmentFlag.AlignCenter,
            "S",
        )

    def sizeHint(self):
        return QSize(180, 220)

    def minimumSizeHint(self):
        return QSize(140, 160)

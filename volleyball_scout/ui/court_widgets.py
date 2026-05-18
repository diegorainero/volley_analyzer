"""Court visualization widgets for live scouting.

Provides:
- TeamCourtWidget: A half-court with 6 player cells (P1-P6) arranged in a 2x3 grid.
- ServeTrajectoryOverlay: Transparent overlay to draw serve/attack trajectories.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from PyQt6.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    QMimeData,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QDrag,
    QFont,
    QPainter,
    QPen,
    QPixmap,
    QCursor,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class LiberoDragLabel(QLabel):
    """A label that can be dragged to swap the libero with a court player."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_pos: QPointF | None = None
        self._libero_num: str | None = None

    def set_libero_number(self, num: str | None):
        self._libero_num = num
        self.setText(num if num else "")
        self.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #FFFFFF;"
            "background-color: #F59E0B; border: 2px solid #D97706; border-radius: 18px;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._drag_start_pos is None:
            return
        if (event.position() - self._drag_start_pos).manhattanLength() < 10:
            return
        if not self._libero_num or self._libero_num == "-":
            return

        drag = QDrag(self)
        mime = QMimeData()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)
        stream.writeString(self._libero_num.encode("utf-8"))
        mime.setData("application/x-libero", data)
        drag.setMimeData(mime)

        pixmap = QPixmap(44, 44)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#F59E0B"))
        p.setPen(QPen(QColor("#D97706"), 2))
        p.drawEllipse(2, 2, 40, 40)
        p.setPen(QColor("#FFFFFF"))
        f = p.font()
        f.setBold(True)
        f.setPointSize(14)
        p.setFont(f)
        p.drawText(QRectF(2, 2, 40, 40), Qt.AlignmentFlag.AlignCenter, self._libero_num)
        p.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(22, 22))

        drag.exec(Qt.DropAction.MoveAction)


class DropCell(QFrame):
    """A court cell that accepts libero drops."""

    def __init__(self, pos_code: str, parent=None):
        super().__init__(parent)
        self.setProperty("pos_code", pos_code)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-libero"):
            event.acceptProposedAction()
            self.setStyleSheet(
                "QFrame { border: 2px dashed #F59E0B; background: rgba(245,158,11,40); }"
            )
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-libero"):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("QFrame { border: none; background: transparent; }")

    def dropEvent(self, event):
        self.setStyleSheet("QFrame { border: none; background: transparent; }")
        if not event.mimeData().hasFormat("application/x-libero"):
            return
        raw = event.mimeData().data("application/x-libero")
        stream = QDataStream(raw, QIODevice.OpenModeFlag.ReadOnly)
        libero_num = stream.readString().decode("utf-8")
        pos_code = self.property("pos_code")
        if pos_code:
            court = self.parentWidget()
            while court is not None and not isinstance(court, TeamCourtWidget):
                court = court.parentWidget()
            if court is not None:
                court._on_libero_dropped(str(pos_code), libero_num)
        event.acceptProposedAction()


class CourtFrame(QFrame):
    """QFrame customizzata che disegna linee campo e cerchi ricezione dopo lo sfondo."""

    def __init__(self, team_side: str, parent=None):
        super().__init__(parent)
        self._team_side = team_side
        self._reception_positions: dict[str, tuple[float, float]] = {}
        self.setStyleSheet(
            "QFrame { background-color: #5D8CD8; }"
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        r = self.rect()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.setPen(QPen(QColor("#FFFFFF"), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(r.adjusted(4, 4, -4, -4))

        three_m_pen = QPen(QColor("#FFFFFF"), 2)
        three_m_pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(three_m_pen)
        if self._team_side == "home":
            x = r.left() + r.width() * 2 / 3.0
        else:
            x = r.left() + r.width() * 1 / 3.0
        ty, by = r.top() + 6, r.bottom() - 6
        p.drawLine(int(x), int(ty), int(x), int(by))

        p.end()


class TeamCourtWidget(QWidget):
    """Half-court displaying player positions in a 2x3 grid.

    Emits cellClicked(side, pos_code, zone, click_x, click_y) on click.
    Emits liberoDropped(side, pos_code, player_number, libero_number) on libero drop.
    """

    VISUAL_GRID_HOME = (("P5", "P4"), ("P6", "P3"), ("P1", "P2"))
    VISUAL_GRID_AWAY = (("P2", "P1"), ("P3", "P6"), ("P4", "P5"))

    POS_TO_ZONE = {"P1": "1", "P2": "2", "P3": "3", "P4": "4", "P5": "5", "P6": "6"}

    cellClicked = pyqtSignal(str, str, str, float, float)
    liberoDropped = pyqtSignal(str, str, str, str)
    liberoRevertRequested = pyqtSignal(str)

    def __init__(self, team_side: str, team_name="Squadra", parent=None):
        super().__init__(parent)
        self.team_side = team_side
        self._number_labels = {}
        self._libero_number: str | None = None
        self._libero_cell_pos: str | None = None
        self._replaced_player: str | None = None
        self._highlight_number = None
        self._clickable = False
        self._cell_frames: dict[str, DropCell] = {}
        self._reception_positions: dict[str, tuple[float, float]] = {}
        self._reception_label_origins: dict[QLabel, tuple[QWidget, QLayout]] = {}
        self._court_frame: CourtFrame | None = None
        self._setup_ui(team_name)
        self._libero_drag_label = LiberoDragLabel(self)
        self._libero_drag_label.setVisible(False)
        self._libero_drag_label.raise_()
        self._replaced_player_label = QPushButton(self)
        self._replaced_player_label.setVisible(False)
        self._replaced_player_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._replaced_player_label.clicked.connect(self._on_reverted_clicked)

    def _visual_grid(self) -> tuple[tuple[str, ...], ...]:
        return (
            self.VISUAL_GRID_AWAY if self.team_side == "away" else self.VISUAL_GRID_HOME
        )

    def _setup_ui(self, team_name: str):
        self.setStyleSheet(
            """
            TeamCourtWidget {
                border: 1px solid #B79C8A;
                border-radius: 10px;
                background-color: #2F241F;
            }
            """
        )

        layout = QVBoxLayout(self)
        if self.team_side == "home":
            layout.setContentsMargins(30, 30, 4, 30)
        else:
            layout.setContentsMargins(4, 30, 30, 30)
        layout.setSpacing(0)

        court_frame = CourtFrame(self.team_side)
        court_layout = QVBoxLayout(court_frame)
        court_layout.setContentsMargins(6, 6, 6, 6)

        grid = QGridLayout()
        grid.setSpacing(6)

        for row, row_positions in enumerate(self._visual_grid()):
            for col, pos_code in enumerate(row_positions):
                cell = DropCell(pos_code)
                cell.setMinimumSize(72, 58)
                cell.setStyleSheet(
                    """
                    QFrame { border: none; background: transparent; }
                    """
                )
                cell_layout = QVBoxLayout(cell)
                cell_layout.setContentsMargins(3, 3, 3, 3)
                cell_layout.setSpacing(0)

                number_label = QLabel("-")
                number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                number_label.setFixedSize(44, 44)
                number_label.setStyleSheet(
                    "font-size: 18px; font-weight: bold; color: #111827;"
                    "background-color: #E5E7EB; border: 1px solid #CBD5E1; border-radius: 22px;"
                )

                cell_layout.addStretch(1)
                cell_layout.addWidget(number_label, 0, Qt.AlignmentFlag.AlignCenter)
                cell_layout.addStretch(1)

                self._number_labels[pos_code] = number_label
                self._cell_frames[pos_code] = cell
                grid.addWidget(cell, row, col)

        court_layout.addLayout(grid)
        layout.addWidget(court_frame)
        self._court_frame = court_frame

    def _update_libero_icon_position(self):
        if not self._court_frame or not self._libero_drag_label.isVisible():
            return
        cf = self._court_frame
        g = cf.geometry()
        size = 36
        x = g.right() - size - 2
        y = g.top() - size // 2 + 2
        self._libero_drag_label.setGeometry(x, y, size, size)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_libero_icon_position()
        self._update_replaced_player_position()
        self._set_reception_label_positions()

    def _normalize_player_number(self, value) -> str | None:
        if value is None:
            return None
        raw = str(value).strip().upper()
        if raw.endswith("P"):
            raw = raw[:-1]
        if not raw or raw == "-":
            return None
        try:
            return str(int(raw))
        except Exception:
            return raw.lstrip("0") or raw

    def _apply_number_style(self, label: QLabel, highlighted: bool, is_libero: bool = False):
        if is_libero:
            label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #FFFFFF;"
                "background-color: #F59E0B; border: 2px solid #D97706; border-radius: 22px;"
            )
        elif highlighted:
            label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #F8FAFC;"
                "background-color: #DC2626; border: 1px solid #7F1D1D; border-radius: 22px;"
            )
        else:
            label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #111827;"
                "background-color: #E5E7EB; border: 1px solid #CBD5E1; border-radius: 22px;"
            )

    def set_highlight_player(self, player_number):
        self._highlight_number = self._normalize_player_number(player_number)
        for label in self._number_labels.values():
            current = self._normalize_player_number(label.text())
            self._apply_number_style(
                label,
                self._highlight_number is not None
                and current == self._highlight_number,
            )

    def clear_highlight(self):
        self._highlight_number = None
        for label in self._number_labels.values():
            current = self._normalize_player_number(label.text())
            is_libero = (
                self._libero_number is not None
                and current == self._libero_number
            )
            self._apply_number_style(label, False, is_libero=is_libero)

    def setClickable(self, enabled: bool):
        self._clickable = enabled

    def update_lineup(
        self,
        team_name: str,
        positions: dict,
        libero=None,
        replaced_player: str | None = None,
        serving=False,
        setter_number: str | None = None,
    ):
        setter_norm = self._normalize_player_number(setter_number)

        # Reset libero cell tracking
        self._libero_cell_pos = None

        for pos_code, label in self._number_labels.items():
            value = positions.get(pos_code) if positions else None
            current_norm = self._normalize_player_number(value)
            if current_norm is None:
                label.setText("-")
            elif setter_norm is not None and current_norm == setter_norm:
                label.setText(f"{current_norm}P")
            else:
                label.setText(str(current_norm))
            current = self._normalize_player_number(label.text())

            is_libero = (
                self._libero_number is not None
                and current == self._libero_number
            )
            if is_libero:
                self._libero_cell_pos = pos_code

            self._apply_number_style(
                label,
                highlighted=self._highlight_number is not None
                and current == self._highlight_number,
                is_libero=is_libero,
            )

        self._libero_number = str(libero).strip() if libero is not None else None
        if self._libero_number and self._libero_number not in ("-", "", "None"):
            self._libero_drag_label.set_libero_number(self._libero_number)
            self._libero_drag_label.setVisible(True)
            self._update_libero_icon_position()
        else:
            self._libero_drag_label.setVisible(False)

        # Replaced player (off-court) label
        self._replaced_player = (
            str(replaced_player).strip() if replaced_player is not None
            and str(replaced_player).strip() not in ("-", "", "None")
            else None
        )
        self._update_replaced_player_label()

    def _update_replaced_player_label(self):
        if self._replaced_player:
            self._replaced_player_label.setText(f"#{self._replaced_player}")
            self._replaced_player_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #F59E0B;"
                "border: 2px solid #F59E0B; border-radius: 14px; padding: 4px 8px;"
                "background-color: rgba(245,158,11,30); min-width: 36px;"
            )
            self._replaced_player_label.setVisible(True)
            self._update_replaced_player_position()
        else:
            self._replaced_player_label.setVisible(False)

    def _update_replaced_player_position(self):
        if not self._court_frame or not self._replaced_player_label.isVisible():
            return
        cf = self._court_frame
        g = cf.geometry()
        size = 36
        if self.team_side == "home":
            x = g.left() - size - 6
            y = g.top() + 4
        else:
            x = g.right() + 6
            y = g.top() + 4
        self._replaced_player_label.setGeometry(x, y, size + 16, size - 4)

    def _on_reverted_clicked(self):
        if self._replaced_player:
            self.liberoRevertRequested.emit(self._replaced_player)

    def get_cell_center(self, pos_code: str):
        cell = self._cell_frames.get(pos_code)
        if cell is None:
            return None
        return cell.geometry().center()

    def mousePressEvent(self, event):
        if not self._clickable or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        pos = event.position()
        px, py = int(pos.x()), int(pos.y())

        # Check if click is on a reparented reception label
        for label, _ in self._reception_label_origins.items():
            if label.isVisible() and label.geometry().contains(px, py):
                for pos_code, nl in self._number_labels.items():
                    if nl is label and pos_code in self.POS_TO_ZONE:
                        zone = self.POS_TO_ZONE[pos_code]
                        self.cellClicked.emit(self.team_side, str(pos_code), zone, pos.x(), pos.y())
                        return
                break

        # Fall through to the underlying cell
        child = self.childAt(px, py)
        if child is None:
            return

        target = child
        while target is not None:
            pos_code = target.property("pos_code")
            if pos_code and pos_code in self.POS_TO_ZONE:
                zone = self.POS_TO_ZONE[pos_code]
                self.cellClicked.emit(self.team_side, str(pos_code), zone, pos.x(), pos.y())
                return
            if target.parent() == self:
                break
            target = target.parentWidget()

        super().mousePressEvent(event)

    def set_reception_positions(self, positions: dict[str, tuple[float, float]] | None):
        prev_count = len(self._reception_label_origins)
        for label, (orig_parent, orig_layout) in self._reception_label_origins.items():
            label.setParent(orig_parent)
            orig_layout.insertWidget(1, label, 0, Qt.AlignmentFlag.AlignCenter)
            label.show()
        self._reception_label_origins.clear()
        self._reception_positions = dict(positions or {})
        if not positions:
            logger.debug("%s set_reception_positions None (restored %d labels)", self.team_side, prev_count)
            return
        logger.debug("%s set_reception_positions %d players, restoring %d",
                      self.team_side, len(positions), prev_count)
        self._set_reception_label_positions()

    def _set_reception_label_positions(self):
        cf = self._court_frame
        if not cf:
            logger.warning("%s _set_reception_label_positions no court_frame", self.team_side)
            return
        g = cf.geometry()
        positioned = 0
        for num, (nx, ny) in self._reception_positions.items():
            target_text = str(num).strip()
            found = False
            for label in self._number_labels.values():
                label_text = label.text().rstrip("P").strip()
                if label_text == target_text:
                    if label.parent() is not self:
                        self._reception_label_origins[label] = (
                            label.parentWidget(), label.parentWidget().layout()
                        )
                        label.setParent(self)
                    cx = g.left() + nx * g.width()
                    cy = g.top() + ny * g.height()
                    label.move(int(cx - 22), int(cy - 22))
                    label.raise_()
                    label.show()
                    positioned += 1
                    found = True
                    break
            if not found:
                logger.debug("%s label not found for player %s", self.team_side, target_text)
        logger.debug("%s positioned %d/%d reception labels", self.team_side, positioned, len(self._reception_positions))
        if positioned == 0 and self._reception_positions:
            logger.warning("%s fallback: no labels could be positioned for %d players",
                           self.team_side, len(self._reception_positions))
            self._fallback_reception_display(g)
        elif positioned < len(self._reception_positions):
            pass  # some labels were positioned, partial match

    def _fallback_reception_display(self, cf_geometry):
        """If reception label positioning fails, draw colored circles via paintEvent."""
        self._reception_draw_positions = dict(self._reception_positions)
        self._reception_draw_geo = cf_geometry
        self.update()

    def _on_libero_dropped(self, pos_code: str, libero_number: str):
        label = self._number_labels.get(pos_code)
        if label is None:
            return
        current_text = label.text()
        current_num = current_text.rstrip("P").strip() if current_text not in ("-", "") else None
        if current_num is None or current_num == "-":
            return
        self.liberoDropped.emit(self.team_side, pos_code, current_num, libero_number)


class ReceptionOverlay(QWidget):
    """Overlay trasparente che disegna i cerchi di ricezione sopra la griglia."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._positions: dict[str, tuple[float, float]] = {}

    def set_positions(self, positions: dict[str, tuple[float, float]] | None):
        self._positions = dict(positions or {})
        self.update()

    def paintEvent(self, event):
        if not self._positions:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        for num, (nx, ny) in self._positions.items():
            cx = nx * w
            cy = ny * h
            r2 = 18
            p.setPen(QPen(QColor("#CBD5E1"), 2))
            p.setBrush(QColor("#E5E7EB"))
            p.drawEllipse(int(cx - r2), int(cy - r2), r2 * 2, r2 * 2)
            p.setPen(QColor("#111827"))
            f = p.font()
            f.setBold(True)
            f.setPointSize(12)
            p.setFont(f)
            p.drawText(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2), Qt.AlignmentFlag.AlignCenter, str(num))
        p.end()


class ServeTrajectoryOverlay(QWidget):
    """Transparent overlay on the full-court container to draw serve/attack lines."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._trajectory: list[QPointF] = []

    def set_trajectory(self, start: QPointF, end: QPointF):
        self._trajectory = [QPointF(start), QPointF(end)]
        self.update()

    def clear_trajectory(self):
        self._trajectory = []
        self.update()

    def paintEvent(self, event):
        if not self._trajectory:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#EF4444"), 3)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawLine(self._trajectory[0], self._trajectory[-1])

        end = self._trajectory[-1]
        start = self._trajectory[0]
        angle = -(
            -(
                float(
                    __import__("math").atan2(end.y() - start.y(), end.x() - start.x())
                )
            )
        )
        arrow_len = 14.0
        arrow_angle = 0.45
        ax1 = end.x() - arrow_len * __import__("math").cos(angle - arrow_angle)
        ay1 = end.y() - arrow_len * __import__("math").sin(angle - arrow_angle)
        ax2 = end.x() - arrow_len * __import__("math").cos(angle + arrow_angle)
        ay2 = end.y() - arrow_len * __import__("math").sin(angle + arrow_angle)
        p.setBrush(QColor("#EF4444"))
        p.drawPolygon(end, QPointF(ax1, ay1), QPointF(ax2, ay2))

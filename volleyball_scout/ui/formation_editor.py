"""Editor drag-and-drop per formazioni di ricezione per rotazione (1-6)."""

from __future__ import annotations

from PyQt6.QtCore import QMimeData, QPoint, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QDrag,
    QFont,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from volleyball_scout.core.rotation import get_current_rotation


PLAYER_COLORS = [
    QColor("#FACC15"),  # giallo
    QColor("#22C55E"),  # verde
    QColor("#3B82F6"),  # blu
    QColor("#EC4899"),  # rosa
    QColor("#A855F7"),  # viola
    QColor("#F97316"),  # arancione
]


class FormationCourtWidget(QWidget):
    """Campo da ricezione che accetta giocatori trascinati e ne mostra le posizioni."""

    R = 18.0

    def __init__(self, team_side: str, parent=None):
        super().__init__(parent)
        self.team_side = "away" if team_side == "away" else "home"
        self._positions: dict[str, tuple[float, float]] = {}
        self._dragging_player: str | None = None
        self._offset = QPoint(0, 0)
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 260)

    def set_positions(self, positions: dict[str, tuple[float, float]] | None):
        self._positions = {}
        for key, value in dict(positions or {}).items():
            try:
                x, y = value
                self._positions[str(key)] = (min(1.0, max(0.0, float(x))), min(1.0, max(0.0, float(y))))
            except Exception:
                continue
        self.update()

    def get_positions(self) -> dict[str, tuple[float, float]]:
        return dict(self._positions)

    def clear_positions(self):
        self._positions = {}
        self.update()

    def _outer_rect(self) -> QRectF:
        m = 12.0
        return QRectF(m, m, max(10.0, self.width() - m * 2), max(10.0, self.height() - m * 2))

    def _team_half_rect(self) -> QRectF:
        outer = self._outer_rect()
        hw = outer.width() / 2.0
        if self.team_side == "home":
            return QRectF(outer.left(), outer.top(), hw, outer.height())
        return QRectF(outer.left() + hw, outer.top(), hw, outer.height())

    def _to_canvas(self, nx: float, ny: float) -> tuple[float, float]:
        half = self._team_half_rect()
        return (half.left() + nx * half.width(), half.top() + ny * half.height())

    def _to_normalized(self, px: float, py: float) -> tuple[float, float]:
        half = self._team_half_rect()
        nx = (px - half.left()) / max(1.0, half.width())
        ny = (py - half.top()) / max(1.0, half.height())
        return (min(1.0, max(0.0, nx)), min(1.0, max(0.0, ny)))

    def _player_at(self, px: float, py: float) -> str | None:
        r2 = self.R * self.R
        for num in reversed(list(self._positions.keys())):
            cx, cy = self._to_canvas(*self._positions[num])
            if (px - cx) ** 2 + (py - cy) ** 2 <= r2:
                return num
        return None

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer = self._outer_rect()
        half = self._team_half_rect()

        p.setPen(QPen(QColor("#8BAFE7"), 1))
        p.setBrush(QColor("#5D8CD8"))
        p.drawRoundedRect(outer, 8, 8)

        p.setPen(QPen(QColor("#0F172A"), 4))
        nx = outer.left() + outer.width() / 2.0
        p.drawLine(int(nx), int(outer.top()), int(nx), int(outer.bottom()))

        p.setPen(QPen(QColor("#F2D2A8"), 1))
        p.setBrush(QColor("#E8A85F"))
        p.drawRect(half)

        p.setPen(QPen(QColor("#F6C98F"), 1, Qt.PenStyle.DashLine))
        for i in (1, 2):
            y = half.top() + (half.height() / 3.0) * i
            p.drawLine(int(half.left()), int(y), int(half.right()), int(y))
        for i in (1, 2):
            x = half.left() + (half.width() / 3.0) * i
            p.drawLine(int(x), int(half.top()), int(x), int(half.bottom()))

        p.setPen(QPen(QColor("#0F172A"), 1))
        for idx, (num, (nx, ny)) in enumerate(self._positions.items()):
            cx, cy = self._to_canvas(nx, ny)
            r = int(self.R)
            color = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
            p.setBrush(color)
            p.drawEllipse(int(cx - r), int(cy - r), r * 2, r * 2)
            p.drawText(
                QRectF(cx - r, cy - r, r * 2, r * 2),
                Qt.AlignmentFlag.AlignCenter,
                str(num),
            )

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        px, py = event.position().x(), event.position().y()
        player = self._player_at(px, py)
        if player is not None:
            self._dragging_player = player
            cx, cy = self._to_canvas(*self._positions[player])
            self._offset = QPoint(int(px - cx), int(py - cy))
            self.update()

    def mouseMoveEvent(self, event):
        if self._dragging_player is None:
            super().mouseMoveEvent(event)
            return
        px, py = event.position().x() - self._offset.x(), event.position().y() - self._offset.y()
        self._positions[self._dragging_player] = self._to_normalized(px, py)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging_player is not None:
            self._dragging_player = None
            self.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            px, py = event.position().x(), event.position().y()
            player = self._player_at(px, py)
            if player is not None:
                del self._positions[player]
                self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        player = event.mimeData().text().strip()
        if not player:
            return
        px, py = event.position().x(), event.position().y()
        self._positions[player] = self._to_normalized(px, py)
        self.update()
        event.acceptProposedAction()


class PlayerListWidget(QListWidget):
    """Lista giocatori trascinabili."""

    def __init__(self, players: list[str], parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        for num in players:
            item = QListWidgetItem(f"  #{num}")
            item.setData(Qt.ItemDataRole.UserRole, str(num))
            item.setSizeHint(self._size_hint())
            self.addItem(item)
        self.setMinimumWidth(110)
        self.setMaximumWidth(140)

    def _size_hint(self):
        from PyQt6.QtCore import QSize
        return QSize(80, 36)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        player = item.data(Qt.ItemDataRole.UserRole) or ""
        mime = QMimeData()
        mime.setText(str(player))
        drag = QDrag(self)
        drag.setMimeData(mime)
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#FACC15"))
        p.setPen(QPen(QColor("#0F172A"), 1))
        p.drawEllipse(2, 2, 36, 36)
        p.drawText(QRectF(2, 2, 36, 36), Qt.AlignmentFlag.AlignCenter, str(player))
        p.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(20, 20))
        drag.exec(Qt.DropAction.CopyAction)


class RotationSelector(QWidget):
    """Barra di selezione rotazione (1-6) con etichetta."""

    rotation_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.addWidget(QLabel("Rotazione:"))
        self._buttons: list[QPushButton] = []
        self._current = 1
        for r in range(1, 7):
            btn = QPushButton(str(r))
            btn.setFixedSize(36, 36)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=r: self._select(v))
            layout.addWidget(btn)
            self._buttons.append(btn)
        layout.addStretch()
        self._update_style()

    def _select(self, rotation: int):
        self._current = rotation
        self._update_style()
        self.rotation_changed.emit(rotation)

    def _update_style(self):
        for i, btn in enumerate(self._buttons):
            r = i + 1
            if r == self._current:
                btn.setStyleSheet(
                    "font-weight: bold; background-color: #E95420; color: white;"
                    "border: 2px solid #C2410C; border-radius: 18px;"
                )
            else:
                btn.setStyleSheet(
                    "background-color: #374151; color: #E5E7EB;"
                    "border: 1px solid #6B7280; border-radius: 18px;"
                )

    def current_rotation(self) -> int:
        return self._current


class FormationEditorDialog(QDialog):
    """Dialog per modificare le formazioni di ricezione per ogni rotazione."""

    def __init__(
        self,
        team_name: str,
        team_side: str,
        players: list[str],
        formations: dict[int, dict[str, tuple[float, float]]] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.team_side = "away" if team_side == "away" else "home"
        self.setWindowTitle(f"Formazioni ricezione - {team_name}")
        self.setMinimumSize(780, 480)

        self._formations: dict[int, dict[str, tuple[float, float]]] = {}
        if formations:
            for r, pos in formations.items():
                try:
                    cr = int(r)
                    self._formations[cr] = dict(pos)
                except Exception:
                    continue

        cv_layout = QVBoxLayout(self)
        cv_layout.setSpacing(8)

        self.rot_selector = RotationSelector(self)
        self.rot_selector.rotation_changed.connect(self._on_rotation_changed)
        cv_layout.addWidget(self.rot_selector)

        body = QHBoxLayout()
        body.setSpacing(10)

        self.court = FormationCourtWidget(team_side, self)
        body.addWidget(self.court, 1)

        side_panel = QVBoxLayout()
        side_panel.setSpacing(6)
        side_label = QLabel("Giocatori\ndisponibili:")
        side_label.setStyleSheet("font-size: 11px;")
        side_panel.addWidget(side_label)

        self.player_list = PlayerListWidget(players, self)
        side_panel.addWidget(self.player_list, 1)

        btn_copy = QPushButton("Copia rot. ←")
        btn_copy.setToolTip("Copia la formazione della rotazione precedente")
        btn_copy.clicked.connect(self._copy_previous_rotation)
        side_panel.addWidget(btn_copy)

        btn_clear = QPushButton("Pulisci campo")
        btn_clear.clicked.connect(self._clear_current)
        side_panel.addWidget(btn_clear)

        body.addLayout(side_panel)
        cv_layout.addLayout(body, 1)

        btn_row = QHBoxLayout()
        self.btn_load_preset = QPushButton("Preset rotazione (R1)")
        self.btn_load_preset.clicked.connect(self._load_preset)
        btn_row.addWidget(self.btn_load_preset)
        btn_row.addStretch()
        save_btn = QPushButton("Salva")
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        cv_layout.addLayout(btn_row)

        self._load_current_rotation()

    def _on_rotation_changed(self, rotation: int):
        self._save_current_rotation()
        self._load_current_rotation()

    def _save_current_rotation(self):
        r = self.rot_selector.current_rotation()
        pos = self.court.get_positions()
        if pos:
            self._formations[r] = pos
        elif r in self._formations:
            del self._formations[r]

    def _load_current_rotation(self):
        r = self.rot_selector.current_rotation()
        self.court.set_positions(self._formations.get(r, {}))

    def _clear_current(self):
        self.court.clear_positions()
        self._save_current_rotation()

    def _copy_previous_rotation(self):
        current = self.rot_selector.current_rotation()
        prev = current - 1 if current > 1 else 6
        src = self._formations.get(prev, {})
        if src:
            self._formations[current] = dict(src)
            self.court.set_positions(dict(src))
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, "Nessuna formazione",
                f"Rotazione {prev} non ha ancora una formazione salvata.",
            )

    def _load_preset(self):
        """Preset base: distribuisce i 6 giocatori nelle 6 zone standard del campo."""
        # Coordinate base per le zone (fila dietro, fila davanti)
        # Back row (zones 5,6,1): y=0.75, x=0.2,0.5,0.8
        # Front row (zones 4,3,2): y=0.25, x=0.2,0.5,0.8
        zones = [
            (0.20, 0.75),  # P5
            (0.50, 0.75),  # P6
            (0.80, 0.75),  # P1
            (0.20, 0.25),  # P4
            (0.50, 0.25),  # P3
            (0.80, 0.25),  # P2
        ]
        players = list(self._formations.get(self.rot_selector.current_rotation(), {}).keys())
        if not players:
            # Prendi dalla lista dei giocatori se non ce ne sono
            from itertools import cycle
            players = []
            for i in range(self.player_list.count()):
                players.append(str(self.player_list.item(i).data(Qt.ItemDataRole.UserRole) or ""))
            players = [p for p in players if p]
            # Se +6, prendi solo i primi 6; se meno, ripeti dal ciclo
            if len(players) < 6:
                c = cycle(players)
                players = [next(c) for _ in range(6)]

        pos = {}
        for i in range(min(6, len(players))):
            pos[players[i]] = zones[i]
        self.court.set_positions(pos)
        self._save_current_rotation()

    def get_formations(self) -> dict[int, dict[str, tuple[float, float]]]:
        self._save_current_rotation()
        return dict(self._formations)

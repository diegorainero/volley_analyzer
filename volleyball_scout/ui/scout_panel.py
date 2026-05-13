import json
import re
from copy import deepcopy

try:
    from volleyball_scout.core.rotation import rotate_lineup_clockwise
except ImportError:
    from ..core.rotation import rotate_lineup_clockwise

from PyQt6.QtCore import QRectF, QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class TeamCourtWidget(QGroupBox):
    """Rappresentazione semplificata del campo per una squadra."""

    VISUAL_GRID_HOME = (("P5", "P4"), ("P6", "P3"), ("P1", "P2"))
    VISUAL_GRID_AWAY = (("P2", "P1"), ("P3", "P6"), ("P4", "P5"))

    def __init__(self, team_side: str, team_name="Squadra", parent=None):
        super().__init__(parent)
        self.team_side = team_side
        self._number_labels = {}
        self._serving_badge = QLabel()
        self._libero_label = QLabel()
        self._highlight_number = None
        self._setup_ui(team_name)

    def _visual_grid(self) -> tuple[tuple[str, ...], ...]:
        return (
            self.VISUAL_GRID_AWAY if self.team_side == "away" else self.VISUAL_GRID_HOME
        )

    def _setup_ui(self, team_name: str):
        self.setTitle(team_name)
        self.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #B79C8A;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #F6EFE9;
                background-color: #2F241F;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        self._serving_badge = QLabel("RICEZIONE")
        self._serving_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._serving_badge.setVisible(False)
        layout.addWidget(self._serving_badge)

        court_frame = QFrame()
        court_frame.setStyleSheet(
            """
            QFrame {
                background-color: #5D8CD8;
                border-radius: 10px;
                border: 1px solid #8BAFE7;
            }
            """
        )
        court_layout = QVBoxLayout(court_frame)
        court_layout.setContentsMargins(6, 6, 6, 6)

        grid = QGridLayout()
        grid.setSpacing(6)

        for row, row_positions in enumerate(self._visual_grid()):
            for col, pos_code in enumerate(row_positions):
                cell = QFrame()
                cell.setMinimumSize(72, 58)
                cell.setStyleSheet(
                    """
                    QFrame {
                        border: none;
                        background: transparent;
                    }
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
                grid.addWidget(cell, row, col)

        court_layout.addLayout(grid)
        layout.addWidget(court_frame)

        self._libero_label = QLabel("Libero: -")
        self._libero_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._libero_label.setStyleSheet(
            "font-size: 11px; color: #EED9C4; padding: 2px 0;"
        )
        layout.addWidget(self._libero_label)

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

    def _apply_number_style(self, label: QLabel, highlighted: bool):
        if highlighted:
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
                label, current is not None and current == self._highlight_number
            )

    def clear_highlight_player(self):
        self._highlight_number = None
        for label in self._number_labels.values():
            self._apply_number_style(label, False)

    def update_lineup(
        self,
        team_name: str,
        positions: dict,
        libero=None,
        serving=False,
        setter_number: str | None = None,
    ):
        self.setTitle(team_name or "Squadra")

        setter_norm = self._normalize_player_number(setter_number)

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
            self._apply_number_style(
                label,
                self._highlight_number is not None
                and current == self._highlight_number,
            )

        libero_text = str(libero) if libero is not None else "-"
        self._libero_label.setText(f"Libero: {libero_text}")

        if serving:
            self._serving_badge.setText("BATTUTA")
            self._serving_badge.setStyleSheet(
                """
                QLabel {
                    background-color: #E95420;
                    color: white;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border: 1px solid #C2410C;
                }
                """
            )
        else:
            self._serving_badge.setText("RICEZIONE")
            self._serving_badge.setStyleSheet(
                """
                QLabel {
                    background-color: #4B5563;
                    color: #F6EFE9;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border: 1px solid #374151;
                }
                """
            )


class ReceptionCourtEditor(QWidget):
    """Editor visuale per posizionare manualmente i giocatori in ricezione."""

    MARKER_RADIUS = 18.0

    def __init__(self, team_side: str, parent=None):
        super().__init__(parent)
        self.team_side = "away" if team_side == "away" else "home"
        self.selected_player: str | None = None
        self._dragging_player: str | None = None
        self._positions: dict[str, tuple[float, float]] = {}
        self.setMinimumSize(520, 280)

    def set_selected_player(self, player_number: str | None):
        self.selected_player = str(player_number) if player_number else None
        self.update()

    def set_positions(self, positions: dict | None):
        self._positions = {}
        for key, value in dict(positions or {}).items():
            try:
                x, y = value
                self._positions[str(key)] = (
                    min(1.0, max(0.0, float(x))),
                    min(1.0, max(0.0, float(y))),
                )
            except Exception:
                continue
        self.update()

    def positions(self) -> dict[str, tuple[float, float]]:
        return dict(self._positions)

    def clear_positions(self):
        self._positions = {}
        self.update()

    def _outer_rect(self) -> QRectF:
        margin = 12.0
        return QRectF(
            margin,
            margin,
            max(10.0, self.width() - margin * 2),
            max(10.0, self.height() - margin * 2),
        )

    def _team_half_rect(self) -> QRectF:
        outer = self._outer_rect()
        half_w = outer.width() / 2.0
        if self.team_side == "home":
            return QRectF(outer.left(), outer.top(), half_w, outer.height())
        return QRectF(outer.left() + half_w, outer.top(), half_w, outer.height())

    def _canvas_point(self, player_number: str) -> tuple[float, float] | None:
        value = self._positions.get(str(player_number))
        if value is None:
            return None

        half = self._team_half_rect()
        nx, ny = value
        return (
            float(half.left() + nx * half.width()),
            float(half.top() + ny * half.height()),
        )

    def _player_at_point(self, px: float, py: float) -> str | None:
        radius_sq = self.MARKER_RADIUS * self.MARKER_RADIUS
        for number in reversed(list(self._positions.keys())):
            center = self._canvas_point(number)
            if center is None:
                continue
            cx, cy = center
            dx = px - cx
            dy = py - cy
            if dx * dx + dy * dy <= radius_sq:
                return number
        return None

    def _set_player_position_from_canvas(
        self, player_number: str, px: float, py: float
    ):
        half = self._team_half_rect()
        clamped_x = min(half.right(), max(half.left(), px))
        clamped_y = min(half.bottom(), max(half.top(), py))

        nx = (clamped_x - half.left()) / max(1.0, half.width())
        ny = (clamped_y - half.top()) / max(1.0, half.height())

        self._positions[str(player_number)] = (
            min(1.0, max(0.0, float(nx))),
            min(1.0, max(0.0, float(ny))),
        )

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        pos = event.position()
        px = float(pos.x())
        py = float(pos.y())
        half = self._team_half_rect()

        clicked_player = self._player_at_point(px, py)
        if clicked_player is not None:
            self.selected_player = clicked_player
            self._dragging_player = clicked_player
            self.update()
            return

        if self.selected_player is None or not half.contains(pos):
            return super().mousePressEvent(event)

        self._dragging_player = self.selected_player
        self._set_player_position_from_canvas(self.selected_player, px, py)
        self.update()

    def mouseMoveEvent(self, event):
        if self._dragging_player is None:
            return super().mouseMoveEvent(event)

        pos = event.position()
        self._set_player_position_from_canvas(
            self._dragging_player,
            float(pos.x()),
            float(pos.y()),
        )
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging_player = None
            self.update()
            return
        return super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer = self._outer_rect()
        half = self._team_half_rect()

        painter.setPen(QPen(QColor("#8BAFE7"), 1))
        painter.setBrush(QColor("#5D8CD8"))
        painter.drawRoundedRect(outer, 8, 8)

        painter.setPen(QPen(QColor("#0F172A"), 4))
        net_x = outer.left() + outer.width() / 2.0
        painter.drawLine(int(net_x), int(outer.top()), int(net_x), int(outer.bottom()))

        painter.setPen(QPen(QColor("#F2D2A8"), 1))
        painter.setBrush(QColor("#E8A85F"))
        painter.drawRect(half)

        painter.setPen(QPen(QColor("#F6C98F"), 1, Qt.PenStyle.DashLine))
        for i in (1, 2):
            y = half.top() + (half.height() / 3.0) * i
            painter.drawLine(int(half.left()), int(y), int(half.right()), int(y))
        for i in (1, 2):
            x = half.left() + (half.width() / 3.0) * i
            painter.drawLine(int(x), int(half.top()), int(x), int(half.bottom()))

        painter.setPen(QPen(QColor("#0F172A"), 1))
        for number, pos in self._positions.items():
            nx, ny = pos
            cx = half.left() + nx * half.width()
            cy = half.top() + ny * half.height()

            radius = int(self.MARKER_RADIUS)
            is_selected = self.selected_player == number
            color = QColor("#FACC15") if is_selected else QColor("#E5E7EB")
            painter.setBrush(color)
            painter.drawEllipse(
                int(cx - radius), int(cy - radius), radius * 2, radius * 2
            )
            painter.drawText(
                QRectF(cx - radius, cy - radius, radius * 2, radius * 2),
                Qt.AlignmentFlag.AlignCenter,
                str(number),
            )


class ReceptionPositionDialog(QDialog):
    def __init__(
        self,
        team_name: str,
        team_side: str,
        players: list[str],
        initial_positions: dict | None = None,
        lineup_positions: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.team_side = "away" if team_side == "away" else "home"
        self._lineup_positions = dict(lineup_positions or {})
        self.setWindowTitle(f"Posizionamento ricezione - {team_name}")
        self.setMinimumSize(680, 430)

        self.editor = ReceptionCourtEditor(team_side, self)
        self.editor.set_positions(initial_positions)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        hint = QLabel(
            "Seleziona il giocatore e clicca/trascina sul campo per posizionare il pallino."
        )
        hint.setStyleSheet("font-size: 11px;")
        layout.addWidget(hint)

        select_row = QHBoxLayout()
        select_row.addWidget(QLabel("Giocatore:"))
        self.player_selector = QComboBox()
        for number in players:
            self.player_selector.addItem(str(number), str(number))
        self.player_selector.currentIndexChanged.connect(self._on_player_changed)
        select_row.addWidget(self.player_selector)

        self.btn_preset_rotation = QPushButton("Preset rotazione")
        self.btn_preset_rotation.clicked.connect(self._apply_rotation_preset)
        select_row.addWidget(self.btn_preset_rotation)

        self.btn_clear_positions = QPushButton("Reset posizioni")
        self.btn_clear_positions.clicked.connect(self.editor.clear_positions)
        select_row.addWidget(self.btn_clear_positions)
        select_row.addStretch()
        layout.addLayout(select_row)

        layout.addWidget(self.editor, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_player_changed(0)

    def _on_player_changed(self, _index: int):
        current = self.player_selector.currentData()
        self.editor.set_selected_player(str(current) if current is not None else None)

    def _apply_rotation_preset(self):
        base_home = {
            "P4": (0.74, 0.20),
            "P3": (0.74, 0.50),
            "P2": (0.74, 0.80),
            "P5": (0.26, 0.20),
            "P6": (0.26, 0.50),
            "P1": (0.26, 0.80),
        }

        preset = {}
        for pos_code, number in self._lineup_positions.items():
            if number is None:
                continue
            code = str(pos_code).strip().upper()
            if code not in base_home:
                continue

            x, y = base_home[code]
            if self.team_side == "away":
                x = 1.0 - x
            preset[str(number)] = (x, y)

        if preset:
            self.editor.set_positions(preset)

    def positions(self) -> dict[str, tuple[float, float]]:
        return self.editor.positions()


class ScoutPanel(QWidget):
    """Schermata Scouting Live con doppio campo allineato."""

    set_finished = pyqtSignal(dict)
    back_requested = pyqtSignal()

    SKILL_CODES = {
        "Attacco": "A",
        "Muro": "B",
        "Battuta": "S",
        "Ricezione": "R",
        "Alzata": "E",
        "Difesa": "D",
    }

    # Tasti rapidi DataVolley (configurabili)
    CODE_SHORTCUTS = [
        ("Battuta", "S"),
        ("Ricezione", "R"),
        ("Alzata", "E"),
        ("Attacco", "A"),
        ("Muro", "B"),
        ("Difesa", "D"),
        ("Punto", "#"),
        ("Errore", "="),
    ]

    KEYPAD_SKILL_TOKENS = ["S", "R", "E", "A", "B", "D", "F"]
    KEYPAD_EVAL_TOKENS = ["#", "+", "!", "-", "=", "/"]
    KEYPAD_DIGIT_ROWS = [("7", "8", "9"), ("4", "5", "6"), ("1", "2", "3"), ("0",)]
    KEYPAD_MACRO_PRESETS = [
        ("Ace", "S#"),
        ("Err. Battuta", "S="),
        ("Pipe Punto", "A#P"),
    ]
    SHORTCUTS_SETTINGS_ORG = "VolleyballScout"
    SHORTCUTS_SETTINGS_APP = "ScoutPanel"
    SHORTCUTS_SETTINGS_KEY = "code_shortcuts"
    KEYPAD_SIZE_SETTINGS_KEY = "code_keypad_size"
    KEYBOARD_MODE_SETTINGS_KEY = "keyboard_only_mode"
    HOTKEY_MAP_SETTINGS_KEY = "keyboard_hotkey_map"
    POINT_OUTCOME_MAP_SETTINGS_KEY = "point_outcome_map"
    POINT_OUTCOME_SCOPE_SETTINGS_KEY = "point_outcome_scope"
    POINT_OUTCOME_MAP_MATCH_PREFIX = "point_outcome_map_match_"
    POINT_OUTCOME_MAP_SET_PREFIX = "point_outcome_map_set_"
    TIMER_SYNC_WITH_VIDEO_SETTINGS_KEY = "timer_sync_with_video"
    VIDEO_MEMORY_SETTINGS_PREFIX = "video_resume_seconds_match_"
    RECEPTION_MEMORY_SETTINGS_PREFIX = "rx_manual_match_"
    HOTKEY_DEFAULTS = {
        "macro_1": "F1",
        "macro_2": "F2",
        "macro_3": "F3",
        "team_a": "F7",
        "team_b": "F8",
        "clear_code": "F9",
        "submit_code": "F10",
    }

    # Alias minimi supportati in input (es. V per battuta)
    DATA_VOLLEY_SKILL_ALIASES = {
        "S": "S",
        "V": "S",
        "R": "R",
        "E": "E",
        "A": "A",
        "B": "B",
        "D": "D",
        "F": "F",
    }

    DATA_VOLLEY_EVALUATIONS = {"#", "+", "!", "-", "=", "/"}

    HISTORY_KIND_POINT = "PT"
    HISTORY_KIND_SKILL = "SK"
    HISTORY_KIND_SYSTEM = "SY"

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_context = {}
        self.serving_side = "home"
        self.rally_history = []
        self.current_set_id = None
        self.event_counter = 0

        self.elapsed_seconds = 0
        self.elapsed_seconds_exact = 0.0
        self.timer_running = False
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_timer_tick)

        self.skill_buttons = []
        self.code_shortcut_buttons = []
        self.code_keypad_buttons = []
        self.code_shortcuts = self._load_shortcuts_config()
        self.keypad_size_mode = self._load_keypad_size_mode()
        self.keyboard_only_mode = self._load_keyboard_mode_enabled()
        self.hotkey_map = self._load_hotkey_map()
        self.point_outcome_scope = self._load_point_outcome_scope()
        self.point_outcome_map = self._load_point_outcome_map()
        self.sync_timer_with_video = self._load_timer_sync_with_video()
        self.history_records = []
        self.timeouts_used = {"home": 0, "away": 0}

        # Sync video -> timestamp evento
        self.video_source_info = {}
        self.video_timestamp_seconds = None
        self.video_widget = None
        self.video_is_live = False
        self.video_paused = False
        self.timer_was_running_before_video_pause = False
        self._resume_video_seconds: float | None = None
        self._last_saved_video_second: int | None = None

        self.history_timestamp_role = int(Qt.ItemDataRole.UserRole) + 1
        self.active_history_event_id: int | None = None

        self.initial_service_selected = False
        self.setter_number_by_side: dict[str, str | None] = {
            "home": None,
            "away": None,
        }
        self.reception_rotation_hint: dict[str, str] = {"home": "-", "away": "-"}
        self.reception_manual_positions: dict[str, dict[str, tuple[float, float]]] = {
            "home": {},
            "away": {},
        }

        self._setup_ui()
        self._set_controls_enabled(False)
        self._reset_timer_ui()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _setup_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        main_panel = QWidget()
        layout = QVBoxLayout(main_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("Scouting Live")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(
            "border: 1px solid #B79C8A; border-radius: 8px; padding: 8px;"
        )
        layout.addWidget(title)

        self.subtitle = QLabel(
            "Conferma una formazione del primo set per iniziare lo scouting"
        )
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.subtitle)

        self.match_info = QLabel("Partita: -")
        self.match_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_info.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.match_info)

        self.video_resume_badge = QLabel("")
        self.video_resume_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_resume_badge.setVisible(False)
        self.video_resume_badge.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #FFF7ED;"
            "background-color: #9A3412; border: 1px solid #C2410C;"
            "border-radius: 8px; padding: 3px 8px;"
        )
        layout.addWidget(self.video_resume_badge)

        self.match_mode_badge = QLabel("")
        self.match_mode_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_mode_badge.setVisible(False)
        self.match_mode_badge.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #ECFDF5;"
            "background-color: #065F46; border: 1px solid #047857;"
            "border-radius: 8px; padding: 3px 8px;"
        )
        layout.addWidget(self.match_mode_badge)

        timer_layout = QHBoxLayout()
        timer_layout.setSpacing(8)
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; border: 1px solid #B79C8A; border-radius: 6px; padding: 4px 10px;"
        )

        self.btn_timer_toggle = QPushButton("Avvia timer")
        self.btn_timer_toggle.clicked.connect(self._toggle_timer)

        self.btn_timer_reset = QPushButton("Reset timer")
        self.btn_timer_reset.clicked.connect(self._reset_timer)

        self.btn_pause_video_scout = QPushButton("Pausa video+scout")
        self.btn_pause_video_scout.setCheckable(True)
        self.btn_pause_video_scout.setEnabled(False)
        self.btn_pause_video_scout.toggled.connect(self._toggle_video_and_timer_pause)

        timer_layout.addStretch()
        timer_layout.addWidget(self.timer_label)
        timer_layout.addWidget(self.btn_timer_toggle)
        timer_layout.addWidget(self.btn_timer_reset)
        timer_layout.addWidget(self.btn_pause_video_scout)
        timer_layout.addStretch()
        layout.addLayout(timer_layout)

        scoreboard_layout = QHBoxLayout()
        scoreboard_layout.setSpacing(10)

        self.home_score = QLabel("0")
        self.home_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.home_score.setStyleSheet(
            "font-size: 18px; font-weight: bold; border: 1px solid #B79C8A; border-radius: 6px; padding: 4px 10px;"
        )

        self.set_info = QLabel("Set 1")
        self.set_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_info.setStyleSheet("font-weight: bold; font-size: 13px;")

        self.away_score = QLabel("0")
        self.away_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.away_score.setStyleSheet(
            "font-size: 18px; font-weight: bold; border: 1px solid #B79C8A; border-radius: 6px; padding: 4px 10px;"
        )

        scoreboard_layout.addStretch()
        scoreboard_layout.addWidget(self.home_score)
        scoreboard_layout.addWidget(self.set_info)
        scoreboard_layout.addWidget(self.away_score)
        scoreboard_layout.addStretch()
        layout.addLayout(scoreboard_layout)

        timeout_layout = QHBoxLayout()
        timeout_layout.setSpacing(12)
        self.timeout_home_label = QLabel("TO Casa: 0/2")
        self.timeout_home_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.timeout_away_label = QLabel("TO Ospiti: 0/2")
        self.timeout_away_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        timeout_layout.addStretch()
        timeout_layout.addWidget(self.timeout_home_label)
        timeout_layout.addWidget(self.timeout_away_label)
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)

        score_buttons_layout = QHBoxLayout()
        score_buttons_layout.setSpacing(8)

        self.btn_point_home = QPushButton("+ Punto Casa")
        self.btn_point_home.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)
        )
        self.btn_point_home.clicked.connect(lambda: self._register_point("home"))

        self.btn_point_away = QPushButton("+ Punto Ospiti")
        self.btn_point_away.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)
        )
        self.btn_point_away.clicked.connect(lambda: self._register_point("away"))

        self.btn_undo = QPushButton("Undo rally")
        self.btn_undo.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
        )
        self.btn_undo.clicked.connect(self._undo_last_rally)

        self.btn_finish_set = QPushButton("Fine Set")
        self.btn_finish_set.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        )
        self.btn_finish_set.clicked.connect(self._finish_set)

        self.btn_finish_match = QPushButton("Fine Incontro")
        self.btn_finish_match.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        )
        self.btn_finish_match.clicked.connect(self._finish_match)

        self.btn_back_to_scouts = QPushButton("Indietro agli scout")
        self.btn_back_to_scouts.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)
        )
        self.btn_back_to_scouts.clicked.connect(self._request_back_to_scouts)

        self.btn_set_actions = QToolButton()
        self.btn_set_actions.setText("Azioni Set")
        self.btn_set_actions.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_set_actions.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.btn_set_actions.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )

        self.set_actions_menu = QMenu(self)
        self.action_timeout_home = self.set_actions_menu.addAction("Timeout Casa")
        self.action_timeout_away = self.set_actions_menu.addAction("Timeout Ospiti")
        self.set_actions_menu.addSeparator()
        self.action_sub_home = self.set_actions_menu.addAction("Sostituzione Casa")
        self.action_sub_away = self.set_actions_menu.addAction("Sostituzione Ospiti")

        self.action_timeout_home.triggered.connect(
            lambda: self._register_timeout("home")
        )
        self.action_timeout_away.triggered.connect(
            lambda: self._register_timeout("away")
        )
        self.action_sub_home.triggered.connect(
            lambda: self._register_substitution("home")
        )
        self.action_sub_away.triggered.connect(
            lambda: self._register_substitution("away")
        )

        self.btn_set_actions.setMenu(self.set_actions_menu)

        score_buttons_layout.addStretch()
        score_buttons_layout.addWidget(self.btn_point_home)
        score_buttons_layout.addWidget(self.btn_point_away)
        score_buttons_layout.addWidget(self.btn_undo)
        score_buttons_layout.addWidget(self.btn_set_actions)
        score_buttons_layout.addWidget(self.btn_finish_set)
        score_buttons_layout.addWidget(self.btn_finish_match)
        score_buttons_layout.addWidget(self.btn_back_to_scouts)
        score_buttons_layout.addStretch()
        layout.addLayout(score_buttons_layout)

        hint = QLabel(
            "Imposta la battuta iniziale a inizio set. Poi servizio/rotazioni vengono gestiti automaticamente."
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-size: 10px; color: #D9CFC5;")
        layout.addWidget(hint)

        initial_service_row = QHBoxLayout()
        initial_service_row.setSpacing(8)
        initial_service_row.addWidget(QLabel("Battuta iniziale:"))

        self.btn_initial_service_home = QPushButton("Casa")
        self.btn_initial_service_home.clicked.connect(
            lambda: self._set_initial_service("home")
        )
        initial_service_row.addWidget(self.btn_initial_service_home)

        self.btn_initial_service_away = QPushButton("Ospiti")
        self.btn_initial_service_away.clicked.connect(
            lambda: self._set_initial_service("away")
        )
        initial_service_row.addWidget(self.btn_initial_service_away)

        self.initial_service_status = QLabel("Seleziona chi batte ad inizio set")
        self.initial_service_status.setStyleSheet("font-size: 10px; color: #EBD8C5;")
        initial_service_row.addWidget(self.initial_service_status, 1)
        layout.addLayout(initial_service_row)

        courts_row = QHBoxLayout()
        courts_row.setSpacing(10)

        self.home_outer_status = QLabel("RICEZIONE")
        self.home_outer_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.home_outer_status.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #F6EFE9;"
            "border: 1px solid #6B7280; border-radius: 8px; padding: 6px 4px;"
            "background-color: #374151;"
        )
        self.home_outer_status.setMinimumWidth(90)

        self.away_outer_status = QLabel("RICEZIONE")
        self.away_outer_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.away_outer_status.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #F6EFE9;"
            "border: 1px solid #6B7280; border-radius: 8px; padding: 6px 4px;"
            "background-color: #374151;"
        )
        self.away_outer_status.setMinimumWidth(90)

        self.home_court = TeamCourtWidget("home", "Casa")
        self.away_court = TeamCourtWidget("away", "Trasferta")

        center_line = QFrame()
        center_line.setFixedWidth(3)
        center_line.setStyleSheet("background-color: #111827; border-radius: 1px;")

        courts_row.addWidget(self.home_outer_status)
        courts_row.addWidget(self.home_court, 1)
        courts_row.addWidget(center_line)
        courts_row.addWidget(self.away_court, 1)
        courts_row.addWidget(self.away_outer_status)
        layout.addLayout(courts_row, 1)

        reception_row = QHBoxLayout()
        reception_row.addStretch()
        self.btn_position_reception = QPushButton("Posiziona ricezione")
        self.btn_position_reception.setToolTip(
            "Scegli la squadra da posizionare in ricezione (Auto/Casa/Ospiti)"
        )
        self.btn_position_reception.clicked.connect(
            self._position_reception_with_prompt
        )
        reception_row.addWidget(self.btn_position_reception)
        reception_row.addStretch()
        layout.addLayout(reception_row)

        datavolley_group = QGroupBox("Codifica DataVolley")
        datavolley_layout = QVBoxLayout(datavolley_group)
        datavolley_layout.setSpacing(8)

        code_input_row = QHBoxLayout()
        code_input_row.setSpacing(6)
        code_input_row.addWidget(QLabel("Squadra:"))

        self.code_team_selector = QComboBox()
        self.code_team_selector.addItem("Casa", "home")
        self.code_team_selector.addItem("Ospiti", "away")
        self.code_team_selector.setToolTip(
            "Squadra associata al codice se non indicata direttamente nel testo"
        )
        code_input_row.addWidget(self.code_team_selector)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Inserisci codice DataVolley (es: a12S#61)")
        self.code_input.returnPressed.connect(self._register_datavolley_code)
        code_input_row.addWidget(self.code_input, 1)

        self.btn_send_code = QPushButton("Invia codice")
        self.btn_send_code.clicked.connect(self._register_datavolley_code)
        code_input_row.addWidget(self.btn_send_code)

        self.btn_clear_code = QPushButton("Pulisci")
        self.btn_clear_code.clicked.connect(self.code_input.clear)
        code_input_row.addWidget(self.btn_clear_code)

        datavolley_layout.addLayout(code_input_row)

        shortcuts_header_row = QHBoxLayout()
        shortcuts_header_row.addWidget(QLabel("Tasti rapidi:"))

        shortcuts_header_row.addWidget(QLabel("Layout:"))
        self.keypad_size_selector = QComboBox()
        self.keypad_size_selector.addItem("Compatto", "compact")
        self.keypad_size_selector.addItem("Grande", "large")
        self.keypad_size_selector.currentIndexChanged.connect(
            self._on_keypad_size_changed
        )
        size_idx = self.keypad_size_selector.findData(self.keypad_size_mode)
        if size_idx >= 0:
            self.keypad_size_selector.setCurrentIndex(size_idx)
        shortcuts_header_row.addWidget(self.keypad_size_selector)

        shortcuts_header_row.addWidget(QLabel("Input:"))
        self.keyboard_mode_selector = QComboBox()
        self.keyboard_mode_selector.addItem("Standard", "normal")
        self.keyboard_mode_selector.addItem("Solo tastiera", "keyboard")
        self.keyboard_mode_selector.currentIndexChanged.connect(
            self._on_keyboard_mode_changed
        )
        mode_idx = self.keyboard_mode_selector.findData(
            "keyboard" if self.keyboard_only_mode else "normal"
        )
        if mode_idx >= 0:
            self.keyboard_mode_selector.setCurrentIndex(mode_idx)
        shortcuts_header_row.addWidget(self.keyboard_mode_selector)

        self.btn_toggle_keypad = QPushButton("Mostra tastierino")
        self.btn_toggle_keypad.setCheckable(True)
        self.btn_toggle_keypad.toggled.connect(self._toggle_keypad_panel)
        shortcuts_header_row.addWidget(self.btn_toggle_keypad)

        shortcuts_header_row.addStretch()
        datavolley_layout.addLayout(shortcuts_header_row)

        self.shortcuts_buttons_widget = QWidget()
        self.shortcuts_layout = QGridLayout(self.shortcuts_buttons_widget)
        self.shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        self.shortcuts_layout.setSpacing(6)
        datavolley_layout.addWidget(self.shortcuts_buttons_widget)

        self._rebuild_code_shortcut_buttons()
        self._create_datavolley_keypad(datavolley_layout)

        self._apply_keyboard_mode_ui()

        layout.addWidget(datavolley_group)

        root_layout.addWidget(main_panel, 3)

        history_panel = QWidget()
        history_side_layout = QVBoxLayout(history_panel)
        history_side_layout.setContentsMargins(0, 0, 0, 0)
        history_side_layout.setSpacing(6)

        self.btn_toggle_codes = QToolButton()
        self.btn_toggle_codes.setCheckable(True)
        self.btn_toggle_codes.setChecked(True)
        self.btn_toggle_codes.setText("Nascondi elenco codici")
        self.btn_toggle_codes.toggled.connect(self._toggle_codes_panel)
        history_side_layout.addWidget(self.btn_toggle_codes)

        self.video_group = QGroupBox("Video")
        self.video_group_layout = QVBoxLayout(self.video_group)
        self.video_group_layout.setContentsMargins(6, 6, 6, 6)
        self.video_group_layout.setSpacing(4)

        self.video_mode_badge = QLabel("Video: OFF")
        self.video_mode_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_mode_badge.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #E5E7EB;"
            "background-color: #374151; border: 1px solid #4B5563;"
            "border-radius: 8px; padding: 3px 8px;"
        )
        self.video_group_layout.addWidget(self.video_mode_badge)

        self.video_placeholder = QLabel("Video non collegato")
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_placeholder.setStyleSheet("font-size: 11px; color: #D9CFC5;")
        self.video_placeholder.setMinimumHeight(140)
        self.video_group_layout.addWidget(self.video_placeholder)
        history_side_layout.addWidget(self.video_group)

        self.codes_group = QGroupBox("Elenco codici")
        history_layout = QVBoxLayout(self.codes_group)

        history_filter_row = QHBoxLayout()
        history_filter_row.addWidget(QLabel("Filtro:"))
        self.history_filter = QComboBox()
        self.history_filter.addItems(["Tutti", "Punti", "Skill", "Sistema"])
        self.history_filter.currentTextChanged.connect(self._apply_history_filter)
        history_filter_row.addWidget(self.history_filter)
        history_filter_row.addStretch()
        history_layout.addLayout(history_filter_row)

        self.events_list = QListWidget()
        self.events_list.setMinimumHeight(240)
        self.events_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.events_list.customContextMenuRequested.connect(
            self._open_events_context_menu
        )
        self.events_list.itemDoubleClicked.connect(self._on_event_item_double_clicked)
        history_layout.addWidget(self.events_list)

        history_side_layout.addWidget(self.codes_group, 1)
        root_layout.addWidget(history_panel, 2)

    def _toggle_codes_panel(self, is_visible: bool):
        self.codes_group.setVisible(is_visible)
        self.btn_toggle_codes.setText(
            "Nascondi elenco codici" if is_visible else "Mostra elenco codici"
        )

    def _toggle_keypad_panel(self, visible: bool):
        if hasattr(self, "datavolley_keypad_group"):
            self.datavolley_keypad_group.setVisible(bool(visible))
        if hasattr(self, "btn_toggle_keypad"):
            self.btn_toggle_keypad.setText(
                "Nascondi tastierino" if visible else "Mostra tastierino"
            )

    def set_video_widget(self, widget: QWidget | None):
        if not hasattr(self, "video_group_layout"):
            return

        if self.video_widget is not None:
            self.video_group_layout.removeWidget(self.video_widget)
            self.video_widget.setParent(None)
            self.video_widget = None

        if widget is None:
            if hasattr(self, "video_placeholder"):
                self.video_placeholder.setVisible(True)
            self._update_video_pause_controls()
            return

        self.video_widget = widget
        self.video_widget.setParent(self.video_group)
        self.video_group_layout.addWidget(self.video_widget, 1)
        if hasattr(self, "video_placeholder"):
            self.video_placeholder.setVisible(False)

        self._update_video_pause_controls()

    def _request_back_to_scouts(self):
        self.back_requested.emit()

    def _set_video_mode_badge(self, text: str, color: str, border: str):
        if not hasattr(self, "video_mode_badge"):
            return
        self.video_mode_badge.setText(text)
        self.video_mode_badge.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #F8FAFC;"
            f"background-color: {color}; border: 1px solid {border};"
            "border-radius: 8px; padding: 3px 8px;"
        )

    def _refresh_video_mode_badge(self):
        source_type = str(self.video_source_info.get("type", "") or "").strip().lower()
        connected = bool(source_type)

        if not connected:
            self._set_video_mode_badge("Video: OFF", "#374151", "#4B5563")
            return

        if self.video_is_live:
            self._set_video_mode_badge("Video: LIVE", "#9A3412", "#C2410C")
            return

        if self.video_paused:
            self._set_video_mode_badge("Video: PAUSA", "#7C2D12", "#EA580C")
            return

        self._set_video_mode_badge("Video: FILE", "#065F46", "#047857")

    def _update_video_pause_controls(self):
        if not hasattr(self, "btn_pause_video_scout"):
            return

        can_pause = (
            self.video_widget is not None
            and not self.video_is_live
            and hasattr(self.video_widget, "set_paused")
        )
        self.btn_pause_video_scout.setEnabled(bool(can_pause))
        if not can_pause and self.btn_pause_video_scout.isChecked():
            self.btn_pause_video_scout.blockSignals(True)
            self.btn_pause_video_scout.setChecked(False)
            self.btn_pause_video_scout.blockSignals(False)
        self.btn_pause_video_scout.setText(
            "Riprendi video+scout"
            if self.btn_pause_video_scout.isChecked()
            else "Pausa video+scout"
        )

    def _toggle_video_and_timer_pause(self, paused: bool):
        if self.video_widget is None or self.video_is_live:
            if hasattr(self, "btn_pause_video_scout"):
                self.btn_pause_video_scout.blockSignals(True)
                self.btn_pause_video_scout.setChecked(False)
                self.btn_pause_video_scout.blockSignals(False)
            return

        if not hasattr(self.video_widget, "set_paused"):
            return

        if paused:
            self.timer_was_running_before_video_pause = bool(self.timer_running)
            if self.timer_running:
                self._toggle_timer()
        else:
            if self.timer_was_running_before_video_pause and not self.timer_running:
                self._toggle_timer()
            self.timer_was_running_before_video_pause = False

        try:
            self.video_widget.set_paused(bool(paused))
        except Exception:
            pass

        self.btn_pause_video_scout.setText(
            "Riprendi video+scout" if paused else "Pausa video+scout"
        )

    def set_video_playback_state(self, state: dict | None):
        payload = dict(state or {})
        self.video_is_live = bool(payload.get("is_live", False))
        self.video_paused = bool(payload.get("paused", False))

        if "seconds" in payload:
            try:
                seconds = float(payload.get("seconds"))
                if seconds >= 0:
                    self.video_timestamp_seconds = seconds
            except Exception:
                pass

        if not self.video_is_live:
            if self.video_paused:
                if self.timer_running:
                    self.timer_was_running_before_video_pause = True
                    self._toggle_timer()
            else:
                if self.timer_was_running_before_video_pause and not self.timer_running:
                    self._toggle_timer()
                self.timer_was_running_before_video_pause = False

        self._update_video_pause_controls()
        self._refresh_video_mode_badge()

        if (
            hasattr(self, "btn_pause_video_scout")
            and self.btn_pause_video_scout.isEnabled()
        ):
            should_checked = bool(self.video_paused)
            if self.btn_pause_video_scout.isChecked() != should_checked:
                self.btn_pause_video_scout.blockSignals(True)
                self.btn_pause_video_scout.setChecked(should_checked)
                self.btn_pause_video_scout.blockSignals(False)
            self.btn_pause_video_scout.setText(
                "Riprendi video+scout" if should_checked else "Pausa video+scout"
            )

        self._highlight_history_by_current_time(scroll_to_active=False)

    def _shortcuts_settings(self) -> QSettings:
        return QSettings(self.SHORTCUTS_SETTINGS_ORG, self.SHORTCUTS_SETTINGS_APP)

    def _video_memory_key(self, match_id) -> str | None:
        try:
            parsed = int(match_id)
            if parsed <= 0:
                return None
            return f"{self.VIDEO_MEMORY_SETTINGS_PREFIX}{parsed}"
        except Exception:
            return None

    def _load_video_resume_seconds(self, match_id) -> float | None:
        key = self._video_memory_key(match_id)
        if key is None:
            return None

        settings = self._shortcuts_settings()
        value = settings.value(key, None)
        if value is None:
            return None

        try:
            return max(0.0, float(value))
        except Exception:
            return None

    def _save_video_resume_seconds(self, seconds: float | None):
        if not self.current_context or seconds is None:
            return

        key = self._video_memory_key(self.current_context.get("match_id"))
        if key is None:
            return

        try:
            value = max(0.0, float(seconds))
        except Exception:
            return

        settings = self._shortcuts_settings()
        settings.setValue(key, f"{value:.3f}")

    def get_video_resume_seconds(self) -> float | None:
        return self._resume_video_seconds

    def _reception_memory_key(self, side: str) -> str | None:
        if not self.current_context:
            return None

        match_id = self.current_context.get("match_id")
        set_number = self.current_context.get("set_number")
        if match_id is None or set_number is None:
            return None

        try:
            parsed_match = int(str(match_id))
            parsed_set = int(str(set_number))
            if parsed_match <= 0 or parsed_set <= 0:
                return None
        except Exception:
            return None

        safe_side = "away" if side == "away" else "home"
        return (
            f"{self.RECEPTION_MEMORY_SETTINGS_PREFIX}{parsed_match}"
            f"_set_{parsed_set}_{safe_side}"
        )

    def _normalize_reception_positions(self, parsed) -> dict[str, tuple[float, float]]:
        if not isinstance(parsed, dict):
            return {}

        result: dict[str, tuple[float, float]] = {}
        for number, value in parsed.items():
            try:
                x, y = value
                result[str(number)] = (
                    min(1.0, max(0.0, float(x))),
                    min(1.0, max(0.0, float(y))),
                )
            except Exception:
                continue
        return result

    def _load_reception_positions_for_side_from_db(
        self, side: str
    ) -> dict[str, tuple[float, float]]:
        if self.db is None or not self.current_context:
            return {}

        match_id = self.current_context.get("match_id")
        set_number = self.current_context.get("set_number")
        if match_id is None or set_number is None:
            return {}

        safe_side = "away" if side == "away" else "home"

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchSetReceptionLayout

                row = (
                    session.query(MatchSetReceptionLayout)
                    .filter_by(
                        match_id=int(match_id),
                        set_number=int(set_number),
                        team_side=safe_side,
                    )
                    .first()
                )
                if row is None or not getattr(row, "positions_json", None):
                    return {}

                parsed = json.loads(str(row.positions_json))
                return self._normalize_reception_positions(parsed)
        except Exception:
            return {}

    def _load_reception_positions_for_side(
        self, side: str
    ) -> dict[str, tuple[float, float]]:
        db_positions = self._load_reception_positions_for_side_from_db(side)
        if db_positions:
            return db_positions

        key = self._reception_memory_key(side)
        if key is None:
            return {}

        settings = self._shortcuts_settings()
        raw = settings.value(key, None)
        if raw is None:
            return {}

        try:
            parsed = json.loads(str(raw))
        except Exception:
            return {}

        normalized = self._normalize_reception_positions(parsed)
        if normalized and self.db is not None and self.current_context:
            self._save_reception_positions_for_side(side, normalized)
        return normalized

    def _save_reception_positions_for_side(
        self, side: str, positions: dict[str, tuple[float, float]]
    ):
        key = self._reception_memory_key(side)

        serializable = {
            str(number): [float(value[0]), float(value[1])]
            for number, value in dict(positions or {}).items()
        }

        if key is not None:
            settings = self._shortcuts_settings()
            settings.setValue(key, json.dumps(serializable, ensure_ascii=False))

        if self.db is None or not self.current_context:
            return

        match_id = self.current_context.get("match_id")
        set_number = self.current_context.get("set_number")
        if match_id is None or set_number is None:
            return

        safe_side = "away" if side == "away" else "home"
        payload = json.dumps(serializable, ensure_ascii=False)

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchSetReceptionLayout

                row = (
                    session.query(MatchSetReceptionLayout)
                    .filter_by(
                        match_id=int(match_id),
                        set_number=int(set_number),
                        team_side=safe_side,
                    )
                    .first()
                )
                if row is None:
                    row = MatchSetReceptionLayout(
                        match_id=int(match_id),
                        set_number=int(set_number),
                        team_side=safe_side,
                        positions_json=payload,
                    )
                    session.add(row)
                else:
                    row.positions_json = payload
        except Exception as e:
            print(f"⚠️ Errore salvataggio layout ricezione su DB: {e}")

    def set_video_resume_badge(self, seconds: float | None):
        if not hasattr(self, "video_resume_badge"):
            return

        if seconds is None:
            self.video_resume_badge.clear()
            self.video_resume_badge.setVisible(False)
            return

        try:
            safe_seconds = max(0, int(float(seconds)))
        except Exception:
            self.video_resume_badge.clear()
            self.video_resume_badge.setVisible(False)
            return

        self.video_resume_badge.setText(
            f"Ripreso da {self._format_seconds(safe_seconds)}"
        )
        self.video_resume_badge.setVisible(True)

    def set_match_mode_badge(
        self,
        *,
        editing_completed_match: bool = False,
        match_status: str | None = None,
    ):
        if not hasattr(self, "match_mode_badge"):
            return

        if editing_completed_match:
            self.match_mode_badge.setText("Modalità modifica match terminato")
            self.match_mode_badge.setVisible(True)
            return

        status = str(match_status or "").strip().lower()
        if status == "completed":
            self.match_mode_badge.setText("Match terminato")
            self.match_mode_badge.setVisible(True)
            return

        self.match_mode_badge.clear()
        self.match_mode_badge.setVisible(False)

    def _load_keypad_size_mode(self) -> str:
        settings = self._shortcuts_settings()
        value = settings.value(self.KEYPAD_SIZE_SETTINGS_KEY, "compact", type=str)
        mode = str(value or "compact").strip().lower()
        return mode if mode in {"compact", "large"} else "compact"

    def _save_keypad_size_mode(self):
        settings = self._shortcuts_settings()
        settings.setValue(self.KEYPAD_SIZE_SETTINGS_KEY, self.keypad_size_mode)

    def _keypad_button_height(self) -> int:
        return 38 if self.keypad_size_mode == "large" else 30

    def _scale_keypad_width(self, base_width: int | None) -> int | None:
        if base_width is None:
            return None
        if self.keypad_size_mode == "large":
            return int(base_width * 1.2)
        return base_width

    def _apply_keypad_size_mode(self):
        min_h = self._keypad_button_height()
        for btn in self.code_keypad_buttons:
            btn.setMinimumHeight(min_h)
            base_width = btn.property("base_max_width")
            if isinstance(base_width, int) and base_width > 0:
                btn.setMaximumWidth(self._scale_keypad_width(base_width) or base_width)

    def _on_keypad_size_changed(self):
        if not hasattr(self, "keypad_size_selector"):
            return

        selected = self.keypad_size_selector.currentData()
        mode = "large" if selected == "large" else "compact"
        self.keypad_size_mode = mode
        self._save_keypad_size_mode()
        self._apply_keypad_size_mode()

    def _load_keyboard_mode_enabled(self) -> bool:
        settings = self._shortcuts_settings()
        value = settings.value(self.KEYBOARD_MODE_SETTINGS_KEY, "0", type=str)
        return str(value or "0").strip() in {"1", "true", "True", "yes"}

    def _save_keyboard_mode_enabled(self):
        settings = self._shortcuts_settings()
        settings.setValue(
            self.KEYBOARD_MODE_SETTINGS_KEY, "1" if self.keyboard_only_mode else "0"
        )

    def _load_timer_sync_with_video(self) -> bool:
        settings = self._shortcuts_settings()
        value = settings.value(self.TIMER_SYNC_WITH_VIDEO_SETTINGS_KEY, "1", type=str)
        return str(value or "1").strip().lower() in {"1", "true", "yes"}

    def _save_timer_sync_with_video(self):
        settings = self._shortcuts_settings()
        settings.setValue(
            self.TIMER_SYNC_WITH_VIDEO_SETTINGS_KEY,
            "1" if self.sync_timer_with_video else "0",
        )

    def _hotkey_action_definitions(self) -> list[tuple[str, str, bool]]:
        macro_1 = (
            self.KEYPAD_MACRO_PRESETS[0][0]
            if len(self.KEYPAD_MACRO_PRESETS) > 0
            else "Macro 1"
        )
        macro_2 = (
            self.KEYPAD_MACRO_PRESETS[1][0]
            if len(self.KEYPAD_MACRO_PRESETS) > 1
            else "Macro 2"
        )
        macro_3 = (
            self.KEYPAD_MACRO_PRESETS[2][0]
            if len(self.KEYPAD_MACRO_PRESETS) > 2
            else "Macro 3"
        )
        return [
            ("macro_1", f"Macro: {macro_1}", False),
            ("macro_2", f"Macro: {macro_2}", False),
            ("macro_3", f"Macro: {macro_3}", False),
            ("team_a", "Team prefisso A", True),
            ("team_b", "Team prefisso B", True),
            ("clear_code", "Pulisci input codice", True),
            ("submit_code", "Invia codice", True),
        ]

    def _normalize_hotkey_token(self, token: str | None) -> str | None:
        value = str(token or "").strip().upper()
        if re.fullmatch(r"F([1-9]|1[0-2])", value):
            return value
        return None

    def _qt_key_to_hotkey_token(self, key: int) -> str | None:
        for idx in range(1, 13):
            qt_key = getattr(Qt.Key, f"Key_F{idx}", None)
            if qt_key is not None and key == int(qt_key):
                return f"F{idx}"
        return None

    def _default_hotkey_map(self) -> dict[str, str]:
        defaults = {}
        valid_actions = {action for action, _, _ in self._hotkey_action_definitions()}
        for action, token in self.HOTKEY_DEFAULTS.items():
            if action in valid_actions:
                normalized = self._normalize_hotkey_token(token)
                if normalized:
                    defaults[action] = normalized
        return defaults

    def _load_hotkey_map(self) -> dict[str, str]:
        settings = self._shortcuts_settings()
        serialized = settings.value(self.HOTKEY_MAP_SETTINGS_KEY, "", type=str) or ""

        result = self._default_hotkey_map()
        valid_actions = {action for action, _, _ in self._hotkey_action_definitions()}

        if serialized.strip():
            for line in serialized.splitlines():
                row = line.strip()
                if not row or "|" not in row:
                    continue
                action, token = row.split("|", 1)
                action = action.strip()
                token_norm = self._normalize_hotkey_token(token)
                if action in valid_actions and token_norm:
                    result[action] = token_norm

        return result

    def _save_hotkey_map(self):
        settings = self._shortcuts_settings()
        lines = []
        for action, _, _ in self._hotkey_action_definitions():
            token = self.hotkey_map.get(action)
            token_norm = self._normalize_hotkey_token(token)
            if token_norm:
                lines.append(f"{action}|{token_norm}")
        settings.setValue(self.HOTKEY_MAP_SETTINGS_KEY, "\n".join(lines))

    def _hotkey_conflicts(
        self, hotkey_map: dict[str, str] | None = None
    ) -> dict[str, list[str]]:
        source_map = hotkey_map or self.hotkey_map
        defaults = self._default_hotkey_map()

        token_to_actions: dict[str, list[str]] = {}
        for action, _, _ in self._hotkey_action_definitions():
            token = source_map.get(action) or defaults.get(action)
            token_norm = self._normalize_hotkey_token(token)
            if not token_norm:
                continue
            token_to_actions.setdefault(token_norm, []).append(action)

        return {
            token: actions
            for token, actions in token_to_actions.items()
            if len(actions) > 1
        }

    def _format_hotkey_conflicts(self, conflicts: dict[str, list[str]]) -> str:
        if not conflicts:
            return ""

        action_labels = {
            action: label for action, label, _ in self._hotkey_action_definitions()
        }
        lines = []
        for token in sorted(conflicts.keys(), key=lambda t: int(t[1:])):
            labels = [action_labels.get(action, action) for action in conflicts[token]]
            lines.append(f"- {token}: " + ", ".join(labels))
        return "\n".join(lines)

    def _active_hotkey_bindings(self) -> dict[str, str]:
        bindings = {}
        defaults = self._default_hotkey_map()
        for action, _, _ in self._hotkey_action_definitions():
            token = self.hotkey_map.get(action) or defaults.get(action)
            token_norm = self._normalize_hotkey_token(token)
            if token_norm and token_norm not in bindings:
                bindings[token_norm] = action
        return bindings

    def _hotkeys_to_text(self, hotkey_map: dict[str, str]) -> str:
        rows = [
            "# Una riga per hotkey (formato: azione=Fx)",
            "# Esempio: macro_1=F1",
            "# IMPORTANTE: non assegnare lo stesso tasto a più azioni",
        ]

        for action, label, keyboard_only in self._hotkey_action_definitions():
            token = self._normalize_hotkey_token(hotkey_map.get(action))
            if token is None:
                token = self._default_hotkey_map().get(action, "")
            scope = "solo tastiera" if keyboard_only else "sempre"
            rows.append(f"{action}={token}   # {label} ({scope})")

        return "\n".join(rows)

    def _parse_hotkeys_text(self, text: str) -> dict[str, str]:
        action_aliases = {
            "macro1": "macro_1",
            "macro_1": "macro_1",
            "macro2": "macro_2",
            "macro_2": "macro_2",
            "macro3": "macro_3",
            "macro_3": "macro_3",
            "teama": "team_a",
            "team_a": "team_a",
            "teamb": "team_b",
            "team_b": "team_b",
            "clear": "clear_code",
            "clear_code": "clear_code",
            "submit": "submit_code",
            "submit_code": "submit_code",
        }

        valid_actions = {action for action, _, _ in self._hotkey_action_definitions()}
        parsed = {}

        for raw_line in str(text or "").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            line = re.sub(r"\s+#.*$", "", line).strip()
            if not line or "=" not in line:
                continue

            action_part, token_part = line.split("=", 1)
            action_raw = action_part.strip().lower()
            token_raw = token_part.strip()

            action = action_aliases.get(action_raw, action_raw)
            if action not in valid_actions:
                continue

            token = self._normalize_hotkey_token(token_raw)
            if not token:
                continue

            parsed[action] = token

        return parsed

    def _configure_hotkeys_map(self):
        current_text = self._hotkeys_to_text(self.hotkey_map)
        new_text, ok = QInputDialog.getMultiLineText(
            self,
            "Mappa hotkeys",
            "Configura la mappa hotkeys (azioni -> tasti funzione):",
            current_text,
        )
        if not ok:
            return

        parsed = self._parse_hotkeys_text(new_text)
        if not parsed:
            QMessageBox.warning(
                self,
                "Mappa hotkeys non valida",
                "Nessuna associazione valida trovata. Usa formato azione=F1.",
            )
            return

        defaults = self._default_hotkey_map()
        merged = dict(defaults)
        merged.update(parsed)

        conflicts = self._hotkey_conflicts(merged)
        if conflicts:
            conflict_text = self._format_hotkey_conflicts(conflicts)
            QMessageBox.warning(
                self,
                "Conflitto hotkeys",
                "Alcuni tasti funzione sono assegnati a più azioni:\n\n"
                f"{conflict_text}\n\n"
                "Correggi la mappa assegnando un tasto univoco per azione.",
            )
            return

        self.hotkey_map = merged
        self._save_hotkey_map()
        self._update_keyboard_hotkeys_hint()
        self._update_hotkeys_map_label()

    def _reset_hotkeys_map(self):
        self.hotkey_map = self._default_hotkey_map()
        self._save_hotkey_map()
        self._update_keyboard_hotkeys_hint()
        self._update_hotkeys_map_label()

    def _default_point_outcome_map(self) -> dict[str, str]:
        return {
            "*#": "self",
            "*=": "opponent",
            "S#": "self",
            "S=": "opponent",
            "R#": "self",
            "R=": "opponent",
        }

    def _point_outcome_scope_options(self) -> list[tuple[str, str]]:
        return [
            ("global", "Globale"),
            ("match", "Solo match corrente"),
            ("set", "Solo set corrente"),
        ]

    def _load_point_outcome_scope(self) -> str:
        settings = self._shortcuts_settings()
        value = settings.value(
            self.POINT_OUTCOME_SCOPE_SETTINGS_KEY, "global", type=str
        )
        scope = str(value or "global").strip().lower()
        valid = {key for key, _ in self._point_outcome_scope_options()}
        return scope if scope in valid else "global"

    def _save_point_outcome_scope(self):
        settings = self._shortcuts_settings()
        settings.setValue(
            self.POINT_OUTCOME_SCOPE_SETTINGS_KEY, self.point_outcome_scope
        )

    def _point_outcome_storage_key(self, scope: str | None = None) -> str:
        chosen = str(scope or self.point_outcome_scope or "global").strip().lower()
        if chosen == "match" and self.current_context:
            match_id = self.current_context.get("match_id")
            if match_id is not None:
                return f"{self.POINT_OUTCOME_MAP_MATCH_PREFIX}{match_id}"
        if chosen == "set" and self.current_context:
            match_id = self.current_context.get("match_id")
            set_number = self.current_context.get("set_number")
            if match_id is not None and set_number is not None:
                return f"{self.POINT_OUTCOME_MAP_SET_PREFIX}{match_id}_{set_number}"
        return self.POINT_OUTCOME_MAP_SETTINGS_KEY

    def _decode_point_outcome_map(self, serialized: str | None) -> dict[str, str]:
        result = dict(self._default_point_outcome_map())
        if not str(serialized or "").strip():
            return result

        for line in str(serialized).splitlines():
            row = line.strip()
            if not row or "|" not in row:
                continue
            key, value = row.split("|", 1)
            key = str(key).strip().upper()
            value = str(value).strip().lower()
            if re.fullmatch(r"[SREABDF\*][#\+!\-=/]", key) and value in {
                "self",
                "opponent",
                "none",
            }:
                result[key] = value
        return result

    def _load_point_outcome_map(self, scope: str | None = None) -> dict[str, str]:
        settings = self._shortcuts_settings()
        key = self._point_outcome_storage_key(scope)
        serialized = settings.value(key, "", type=str)
        return self._decode_point_outcome_map(serialized)

    def _save_point_outcome_map(self, scope: str | None = None):
        settings = self._shortcuts_settings()
        lines = []
        for key in sorted(self.point_outcome_map.keys()):
            value = str(self.point_outcome_map.get(key, "none")).strip().lower()
            if value in {"self", "opponent", "none"} and re.fullmatch(
                r"[SREABDF\*][#\+!\-=/]", key
            ):
                lines.append(f"{key}|{value}")

        storage_key = self._point_outcome_storage_key(scope)
        settings.setValue(storage_key, "\n".join(lines))

    def _point_outcome_map_to_text(self, rules: dict[str, str]) -> str:
        rows = [
            "# Formato: SkillValutazione=esito",
            "# Esito: self | opponent | none",
            "# Esempi:",
            "# S#=self      -> punto a chi esegue la battuta",
            "# R==opponent  -> errore ricezione, punto all'avversario",
            "# *#=self      -> fallback per qualsiasi skill con #",
            "",
        ]

        for key in sorted(rules.keys()):
            rows.append(f"{key}={rules[key]}")
        return "\n".join(rows)

    def _parse_point_outcome_map_text(self, text: str) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for raw_line in str(text or "").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            line = re.sub(r"\s+#.*$", "", line).strip()
            if not line or "=" not in line:
                continue

            m = re.fullmatch(
                r"([SREABDF\*])([#\+!\-=/])\s*=\s*(self|opponent|none)",
                line,
                flags=re.IGNORECASE,
            )
            if not m:
                continue

            skill_token = m.group(1).upper()
            eval_token = m.group(2)
            outcome = m.group(3).lower()
            parsed[f"{skill_token}{eval_token}"] = outcome

        return parsed

    def _configure_point_outcome_map(self):
        current_text = self._point_outcome_map_to_text(self.point_outcome_map)
        new_text, ok = QInputDialog.getMultiLineText(
            self,
            "Mappa punto vinto/perso",
            "Configura le regole punto (Skill+Valutazione -> esito)",
            current_text,
        )
        if not ok:
            return

        parsed = self._parse_point_outcome_map_text(new_text)
        if not parsed:
            QMessageBox.warning(
                self,
                "Mappa non valida",
                "Nessuna regola valida trovata. Usa formato S#=self o R==opponent.",
            )
            return

        self.point_outcome_map = parsed
        self._save_point_outcome_map()

    def _shortcuts_preview_text(self) -> str:
        if not self.code_shortcuts:
            return "Tasti rapidi codifica: -"
        preview = [f"{label}→{token}" for label, token in self.code_shortcuts[:6]]
        suffix = " ..." if len(self.code_shortcuts) > 6 else ""
        return "Tasti rapidi codifica: " + " | ".join(preview) + suffix

    def _hotkeys_preview_text(self) -> str:
        bindings = self._active_hotkey_bindings()
        if not bindings:
            return "Hotkeys: -"
        action_labels = {
            action: label for action, label, _ in self._hotkey_action_definitions()
        }
        ordered = sorted(bindings.keys(), key=lambda t: int(t[1:]))
        items = [
            f"{tok}={action_labels.get(bindings[tok], bindings[tok])}"
            for tok in ordered
        ]
        return "Hotkeys: " + " | ".join(items)

    def _point_outcome_preview_text(self) -> str:
        scope_label = dict(self._point_outcome_scope_options()).get(
            self.point_outcome_scope, self.point_outcome_scope
        )
        keys = sorted(self.point_outcome_map.keys())
        if not keys:
            return f"Mappa punti ({scope_label}): -"
        sample = [f"{k}={self.point_outcome_map[k]}" for k in keys[:8]]
        suffix = " ..." if len(keys) > 8 else ""
        return f"Mappa punti ({scope_label}): " + " | ".join(sample) + suffix

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Impostazioni Scouting")
        dialog.setMinimumWidth(520)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(8)

        title = QLabel("Configura scorciatoie e logica punteggio")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        lbl_shortcuts = QLabel("")
        lbl_shortcuts.setWordWrap(True)
        lbl_shortcuts.setStyleSheet("font-size: 10px; color: #D9CFC5;")
        layout.addWidget(lbl_shortcuts)

        lbl_hotkeys = QLabel("")
        lbl_hotkeys.setWordWrap(True)
        lbl_hotkeys.setStyleSheet("font-size: 10px; color: #D9CFC5;")
        layout.addWidget(lbl_hotkeys)

        scope_row = QHBoxLayout()
        scope_row.addWidget(QLabel("Scope mappa punti:"))
        cmb_scope = QComboBox()
        for scope_key, scope_label in self._point_outcome_scope_options():
            cmb_scope.addItem(scope_label, scope_key)
        idx_scope = cmb_scope.findData(self.point_outcome_scope)
        if idx_scope >= 0:
            cmb_scope.setCurrentIndex(idx_scope)
        scope_row.addWidget(cmb_scope)
        scope_row.addStretch()
        layout.addLayout(scope_row)

        chk_sync_timer = QCheckBox("Sincronizza sempre timer scouting con tempo video")
        chk_sync_timer.setChecked(bool(self.sync_timer_with_video))
        layout.addWidget(chk_sync_timer)

        copy_row = QHBoxLayout()
        copy_row.addStretch()
        btn_copy_global = QPushButton("Duplica regole globali → scope corrente")
        copy_row.addWidget(btn_copy_global)
        copy_row.addStretch()
        layout.addLayout(copy_row)

        lbl_points = QLabel("")
        lbl_points.setWordWrap(True)
        lbl_points.setStyleSheet("font-size: 10px; color: #D9CFC5;")
        layout.addWidget(lbl_points)

        def refresh_preview_labels():
            lbl_shortcuts.setText(self._shortcuts_preview_text())
            lbl_hotkeys.setText(self._hotkeys_preview_text())
            lbl_points.setText(self._point_outcome_preview_text())

            is_global_scope = self.point_outcome_scope == "global"
            btn_copy_global.setEnabled(not is_global_scope)
            btn_copy_global.setToolTip(
                "Seleziona prima scope Match o Set"
                if is_global_scope
                else "Copia la mappa globale nello scope corrente"
            )

        def on_scope_changed():
            selected = cmb_scope.currentData()
            new_scope = str(selected or "global").strip().lower()
            self.point_outcome_scope = new_scope
            self._save_point_outcome_scope()
            self.point_outcome_map = self._load_point_outcome_map()
            refresh_preview_labels()

        def duplicate_global_rules_to_current_scope():
            if self.point_outcome_scope == "global":
                QMessageBox.information(
                    dialog,
                    "Scope globale selezionato",
                    "Seleziona prima scope Match o Set per duplicare le regole globali.",
                )
                return

            global_rules = self._load_point_outcome_map("global")
            self.point_outcome_map = dict(global_rules)
            self._save_point_outcome_map()
            refresh_preview_labels()

            scope_label = dict(self._point_outcome_scope_options()).get(
                self.point_outcome_scope, self.point_outcome_scope
            )
            QMessageBox.information(
                dialog,
                "Regole duplicate",
                f"Regole globali copiate nello scope: {scope_label}.",
            )

        cmb_scope.currentIndexChanged.connect(lambda _i: on_scope_changed())
        btn_copy_global.clicked.connect(duplicate_global_rules_to_current_scope)

        def run_and_refresh(callback):
            callback()
            refresh_preview_labels()

        def on_sync_timer_changed(state: int):
            self.sync_timer_with_video = state == int(Qt.CheckState.Checked)
            self._save_timer_sync_with_video()

        chk_sync_timer.stateChanged.connect(on_sync_timer_changed)

        btn_shortcuts = QPushButton("Configura tasti rapidi codifica")
        btn_shortcuts.clicked.connect(
            lambda: run_and_refresh(self._configure_code_shortcuts)
        )
        layout.addWidget(btn_shortcuts)

        btn_shortcuts_reset = QPushButton("Reset tasti rapidi codifica")
        btn_shortcuts_reset.clicked.connect(
            lambda: run_and_refresh(self._reset_code_shortcuts)
        )
        layout.addWidget(btn_shortcuts_reset)

        btn_hotkeys = QPushButton("Mappa hotkeys tastiera")
        btn_hotkeys.clicked.connect(
            lambda: run_and_refresh(self._configure_hotkeys_map)
        )
        layout.addWidget(btn_hotkeys)

        btn_hotkeys_reset = QPushButton("Reset hotkeys tastiera")
        btn_hotkeys_reset.clicked.connect(
            lambda: run_and_refresh(self._reset_hotkeys_map)
        )
        layout.addWidget(btn_hotkeys_reset)

        btn_points = QPushButton("Mappa punto vinto/perso")
        btn_points.clicked.connect(
            lambda: run_and_refresh(self._configure_point_outcome_map)
        )
        layout.addWidget(btn_points)

        refresh_preview_labels()

        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_box.rejected.connect(dialog.reject)
        close_box.accepted.connect(dialog.accept)
        close_box.button(QDialogButtonBox.StandardButton.Close).clicked.connect(
            dialog.accept
        )
        layout.addWidget(close_box)

        dialog.exec()

    def _update_hotkeys_map_label(self):
        if not hasattr(self, "hotkeys_map_label"):
            return

        bindings = self._active_hotkey_bindings()
        token_to_action = {token: action for token, action in bindings.items()}
        action_labels = {
            action: label for action, label, _ in self._hotkey_action_definitions()
        }

        entries = []
        for token in sorted(token_to_action.keys(), key=lambda t: int(t[1:])):
            action = token_to_action[token]
            label = action_labels.get(action, action)
            entries.append(f"{token} → {label}")

        base_text = "Mappa attiva: " + " | ".join(entries)
        conflicts = self._hotkey_conflicts()
        if conflicts:
            base_text += "  |  ⚠ Conflitti: " + self._format_hotkey_conflicts(
                conflicts
            ).replace("\n", " ; ")

        self.hotkeys_map_label.setText(base_text)

    def _update_keyboard_hotkeys_hint(self):
        if not hasattr(self, "keyboard_hotkeys_hint"):
            return

        action_labels = {
            action: label for action, label, _ in self._hotkey_action_definitions()
        }
        bindings = self._active_hotkey_bindings()

        ordered_tokens = sorted(bindings.keys(), key=lambda t: int(t[1:]))
        preview = [
            f"{token}={action_labels.get(bindings[token], bindings[token])}"
            for token in ordered_tokens
        ]

        prefix = "Modo tastiera" if self.keyboard_only_mode else "Hotkeys"
        self.keyboard_hotkeys_hint.setText(f"{prefix}: " + " | ".join(preview))

    def _apply_keyboard_mode_ui(self):
        self._update_keyboard_hotkeys_hint()
        self._update_hotkeys_map_label()

        if hasattr(self, "code_input"):
            if self.keyboard_only_mode:
                self.code_input.setPlaceholderText(
                    "Modo tastiera: digita codice (Invio=Invia, F-keys=azioni)"
                )
            else:
                self.code_input.setPlaceholderText(
                    "Inserisci codice DataVolley (es: a12S#61)"
                )

        if hasattr(self, "btn_toggle_keypad"):
            self.btn_toggle_keypad.setEnabled(not self.keyboard_only_mode)
            if self.keyboard_only_mode:
                self.btn_toggle_keypad.setChecked(False)
                self._toggle_keypad_panel(False)

    def _on_keyboard_mode_changed(self):
        if not hasattr(self, "keyboard_mode_selector"):
            return

        selected = self.keyboard_mode_selector.currentData()
        self.keyboard_only_mode = selected == "keyboard"
        self._save_keyboard_mode_enabled()
        self._apply_keyboard_mode_ui()

        if self.keyboard_only_mode and hasattr(self, "code_input"):
            self.code_input.setFocus()

    def _execute_hotkey_action(self, action: str) -> bool:
        if action.startswith("macro_"):
            try:
                idx = int(action.split("_", 1)[1]) - 1
            except Exception:
                return False
            if 0 <= idx < len(self.KEYPAD_MACRO_PRESETS):
                _, token = self.KEYPAD_MACRO_PRESETS[idx]
                self._apply_macro_preset(token)
                self._feedback_code_submission(True, f"Macro applicata: {token}")
                return True
            return False

        if (
            action in {"team_a", "team_b", "clear_code", "submit_code"}
            and not self.keyboard_only_mode
        ):
            return False

        if action == "team_a":
            self._set_or_replace_team_prefix("A")
            self._feedback_code_submission(True, "Team prefisso: A")
            return True

        if action == "team_b":
            self._set_or_replace_team_prefix("B")
            self._feedback_code_submission(True, "Team prefisso: B")
            return True

        if action == "clear_code":
            if hasattr(self, "code_input"):
                self.code_input.clear()
            self._clear_player_highlight()
            self._feedback_code_submission(True, "Input codice pulito")
            return True

        if action == "submit_code":
            self._register_datavolley_code()
            return True

        return False

    def _handle_function_hotkey(self, key: int) -> bool:
        token = self._qt_key_to_hotkey_token(key)
        if token is None:
            return False

        action = self._active_hotkey_bindings().get(token)
        if not action:
            return False

        return self._execute_hotkey_action(action)

    def _shortcuts_to_text(self, shortcuts: list[tuple[str, str]]) -> str:
        rows = [
            "# Una riga per bottone (formato: Etichetta=Token)",
            "# Esempio: Battuta=S",
        ]
        for label, token in shortcuts:
            rows.append(f"{label}={token}")
        return "\n".join(rows)

    def _parse_shortcuts_text(self, text: str) -> list[tuple[str, str]]:
        result = []
        for raw_line in str(text or "").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                label_part, token_part = line.split("=", 1)
            elif "->" in line:
                label_part, token_part = line.split("->", 1)
            else:
                label_part, token_part = line, line

            label = label_part.strip()
            token = token_part.strip().upper()
            if not label or not token:
                continue

            if not re.fullmatch(r"[A-Z0-9#\+!\-=/\*]{1,4}", token):
                continue

            result.append((label, token))
            if len(result) >= 24:
                break

        return result

    def _save_shortcuts_config(self):
        settings = self._shortcuts_settings()
        serialized = "\n".join(
            f"{label}|{token}" for label, token in self.code_shortcuts
        )
        settings.setValue(self.SHORTCUTS_SETTINGS_KEY, serialized)

    def _load_shortcuts_config(self) -> list[tuple[str, str]]:
        settings = self._shortcuts_settings()
        serialized = settings.value(self.SHORTCUTS_SETTINGS_KEY, "", type=str) or ""
        if not serialized.strip():
            return list(self.CODE_SHORTCUTS)

        parsed = []
        for line in serialized.splitlines():
            row = line.strip()
            if not row:
                continue
            if "|" in row:
                label, token = row.split("|", 1)
                label = label.strip()
                token = token.strip().upper()
                if label and token:
                    parsed.append((label, token))

        return parsed or list(self.CODE_SHORTCUTS)

    def _rebuild_code_shortcut_buttons(self):
        if not hasattr(self, "shortcuts_layout"):
            return

        while self.shortcuts_layout.count():
            item = self.shortcuts_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.code_shortcut_buttons.clear()

        shortcuts = self.code_shortcuts or list(self.CODE_SHORTCUTS)
        for idx, (label, token) in enumerate(shortcuts):
            btn = QPushButton(f"{label} → {token}")
            btn.setMinimumHeight(34)
            btn.clicked.connect(lambda _, t=token: self._insert_code_token(t))
            self.code_shortcut_buttons.append(btn)
            self.shortcuts_layout.addWidget(btn, idx // 4, idx % 4)

    def _configure_code_shortcuts(self):
        current_text = self._shortcuts_to_text(self.code_shortcuts)
        new_text, ok = QInputDialog.getMultiLineText(
            self,
            "Configura tasti rapidi",
            "Definisci i bottoni rapidi (una riga per bottone):",
            current_text,
        )
        if not ok:
            return

        parsed = self._parse_shortcuts_text(new_text)
        if not parsed:
            QMessageBox.warning(
                self,
                "Configurazione non valida",
                "Nessun bottone valido trovato. Usa formato Etichetta=Token (es. Battuta=S).",
            )
            return

        self.code_shortcuts = parsed
        self._save_shortcuts_config()
        self._rebuild_code_shortcut_buttons()

    def _reset_code_shortcuts(self):
        self.code_shortcuts = list(self.CODE_SHORTCUTS)
        self._save_shortcuts_config()
        self._rebuild_code_shortcut_buttons()

    def _create_keypad_button(
        self,
        text: str,
        on_click,
        *,
        min_h: int | None = None,
        max_w: int | None = None,
    ) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(min_h or self._keypad_button_height())

        btn.setProperty("base_max_width", int(max_w or 0))
        scaled_max_w = self._scale_keypad_width(max_w)
        if scaled_max_w is not None:
            btn.setMaximumWidth(scaled_max_w)

        btn.clicked.connect(on_click)
        self.code_keypad_buttons.append(btn)
        return btn

    def _set_or_replace_team_prefix(self, prefix: str):
        if not hasattr(self, "code_input"):
            return

        current = self.code_input.text().strip().upper()
        if current and current[0] in {"A", "B", "*"}:
            current = current[1:]

        self.code_input.setText(f"{prefix}{current}")
        self.code_input.setFocus()
        self.code_input.setCursorPosition(len(self.code_input.text()))

    def _remove_last_code_char(self):
        if not hasattr(self, "code_input"):
            return
        current = self.code_input.text()
        self.code_input.setText(current[:-1])
        self.code_input.setFocus()
        self.code_input.setCursorPosition(len(self.code_input.text()))

    def _apply_macro_preset(self, token: str):
        if not hasattr(self, "code_input"):
            return

        token = str(token or "").strip().upper()
        if not token:
            return

        current = self.code_input.text().strip().upper()
        base_match = re.match(r"^([AB\*]?\d{0,2})", current)
        base_prefix = base_match.group(1) if base_match else ""

        if base_prefix and len(base_prefix) < len(current):
            self.code_input.setText(f"{base_prefix}{token}")
        elif current and current.isdigit():
            self.code_input.setText(f"{current}{token}")
        elif current and current[0] in {"A", "B", "*"} and len(current) <= 2:
            self.code_input.setText(f"{current}{token}")
        else:
            self.code_input.setText(token)

        self.code_input.setFocus()
        self.code_input.setCursorPosition(len(self.code_input.text()))

    def _create_datavolley_keypad(self, parent_layout: QVBoxLayout):
        keypad_group = QGroupBox("Tastierino DataVolley")
        self.datavolley_keypad_group = keypad_group
        keypad_layout = QVBoxLayout(keypad_group)
        keypad_layout.setSpacing(6)

        team_row = QHBoxLayout()
        team_row.addWidget(QLabel("Team:"))
        team_row.addWidget(
            self._create_keypad_button(
                "a", lambda: self._set_or_replace_team_prefix("A"), max_w=44
            )
        )
        team_row.addWidget(
            self._create_keypad_button(
                "b", lambda: self._set_or_replace_team_prefix("B"), max_w=44
            )
        )
        team_row.addWidget(
            self._create_keypad_button(
                "*", lambda: self._set_or_replace_team_prefix("*"), max_w=44
            )
        )
        team_row.addStretch()
        keypad_layout.addLayout(team_row)

        skill_row = QHBoxLayout()
        skill_row.addWidget(QLabel("Skill:"))
        for token in self.KEYPAD_SKILL_TOKENS:
            skill_row.addWidget(
                self._create_keypad_button(
                    token,
                    lambda checked=False, t=token: self._insert_code_token(t),
                    max_w=44,
                )
            )
        skill_row.addStretch()
        keypad_layout.addLayout(skill_row)

        eval_row = QHBoxLayout()
        eval_row.addWidget(QLabel("Val:"))
        for token in self.KEYPAD_EVAL_TOKENS:
            eval_row.addWidget(
                self._create_keypad_button(
                    token,
                    lambda checked=False, t=token: self._insert_code_token(t),
                    max_w=44,
                )
            )
        eval_row.addStretch()
        keypad_layout.addLayout(eval_row)

        macro_row = QHBoxLayout()
        macro_row.addWidget(QLabel("Macro:"))
        for label, token in self.KEYPAD_MACRO_PRESETS:
            btn = self._create_keypad_button(
                label,
                lambda checked=False, t=token: self._apply_macro_preset(t),
                max_w=110,
            )
            btn.setToolTip(f"Imposta codice rapido: {token}")
            macro_row.addWidget(btn)
        macro_row.addStretch()
        keypad_layout.addLayout(macro_row)

        digits_box = QHBoxLayout()
        digits_box.setSpacing(8)

        digits_grid = QGridLayout()
        digits_grid.setSpacing(4)
        for row_idx, row_tokens in enumerate(self.KEYPAD_DIGIT_ROWS):
            for col_idx, token in enumerate(row_tokens):
                btn = self._create_keypad_button(
                    token,
                    lambda checked=False, t=token: self._insert_code_token(t),
                    max_w=44,
                )
                digits_grid.addWidget(btn, row_idx, col_idx)

        digits_box.addLayout(digits_grid)

        actions_col = QVBoxLayout()
        actions_col.setSpacing(4)
        actions_col.addWidget(
            self._create_keypad_button("⌫", self._remove_last_code_char, max_w=76)
        )
        actions_col.addWidget(
            self._create_keypad_button("Pulisci", self.code_input.clear, max_w=76)
        )
        actions_col.addWidget(
            self._create_keypad_button(
                "Invia", self._register_datavolley_code, max_w=76
            )
        )
        actions_col.addStretch()

        digits_box.addLayout(actions_col)
        digits_box.addStretch()
        keypad_layout.addLayout(digits_box)

        keypad_group.setVisible(False)
        parent_layout.addWidget(keypad_group)
        self._apply_keypad_size_mode()

        if hasattr(self, "btn_toggle_keypad"):
            self.btn_toggle_keypad.setChecked(False)
            self._toggle_keypad_panel(False)

    def _insert_code_token(self, token: str):
        if not hasattr(self, "code_input"):
            return

        current = self.code_input.text().strip()
        if current:
            self.code_input.setText(f"{current}{token}")
        else:
            self.code_input.setText(token)
        self.code_input.setFocus()
        self.code_input.setCursorPosition(len(self.code_input.text()))

    def _append_code_char(self, char: str):
        if not hasattr(self, "code_input"):
            return

        current = self.code_input.text()
        self.code_input.setText(f"{current}{char}")
        self.code_input.setFocus()
        self.code_input.setCursorPosition(len(self.code_input.text()))

    def keyPressEvent(self, event):
        if not self.current_context or not hasattr(self, "code_input"):
            super().keyPressEvent(event)
            return

        key = event.key()
        if self._handle_function_hotkey(key):
            event.accept()
            return

        mods = event.modifiers()
        if mods & (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        ):
            super().keyPressEvent(event)
            return

        focus_widget = self.focusWidget()
        if isinstance(focus_widget, QLineEdit) and focus_widget is not self.code_input:
            super().keyPressEvent(event)
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._register_datavolley_code()
            event.accept()
            return

        if key == Qt.Key.Key_Escape:
            self.code_input.clear()
            self._clear_player_highlight()
            event.accept()
            return

        if key == Qt.Key.Key_Backspace and focus_widget is not self.code_input:
            current = self.code_input.text()
            self.code_input.setText(current[:-1])
            self.code_input.setCursorPosition(len(self.code_input.text()))
            event.accept()
            return

        text = event.text() or ""
        if text and re.fullmatch(r"[A-Za-z0-9#\+!\-=/\*]", text):
            self._append_code_char(text.upper())
            event.accept()
            return

        super().keyPressEvent(event)

    def _selected_code_team_side(self) -> str:
        if hasattr(self, "code_team_selector"):
            selected = self.code_team_selector.currentData()
            if selected in {"home", "away"}:
                return selected
        return "home"

    def _set_code_team_side(self, side: str):
        if not hasattr(self, "code_team_selector"):
            return

        idx = self.code_team_selector.findData("away" if side == "away" else "home")
        if idx >= 0:
            self.code_team_selector.setCurrentIndex(idx)

    def _persist_current_match_video_path(self, video_path: str | None):
        if self.db is None or not self.current_context or not video_path:
            return

        match_id = self.current_context.get("match_id")
        if match_id is None:
            return

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import Match

                match = session.query(Match).filter_by(id=int(match_id)).first()
                if match is not None:
                    match.video_path = str(video_path)
        except Exception as e:
            print(f"⚠️ Errore salvataggio video_path match: {e}")

    def set_video_source(self, source_info: dict | None):
        """Riceve info sorgente video dal player (file/webcam/ip)."""
        self.video_source_info = dict(source_info or {})

        source_type = str(self.video_source_info.get("type", "")).strip()
        source_value = str(self.video_source_info.get("value", "") or "").strip()
        self.video_is_live = source_type in {"webcam", "ip"}

        # Salva path video definitivo quando disponibile (recording) oppure file locale.
        persisted_video_path = ""
        recorded_path_raw = self.video_source_info.get("recorded_path")
        recorded_path = str(recorded_path_raw).strip() if recorded_path_raw else ""
        if recorded_path:
            persisted_video_path = recorded_path
        elif source_type == "file" and source_value:
            persisted_video_path = source_value

        if persisted_video_path:
            if self.current_context is not None:
                self.current_context["video_path"] = persisted_video_path
            self._persist_current_match_video_path(persisted_video_path)

        is_recording = bool(self.video_source_info.get("recording", False))
        if is_recording:
            self.video_timestamp_seconds = 0.0
            if self.sync_timer_with_video:
                self.elapsed_seconds_exact = 0.0
                self.elapsed_seconds = 0
                self.timer_label.setText(self._format_elapsed())
            self._resume_video_seconds = 0.0
            self._last_saved_video_second = 0

        self._update_video_pause_controls()
        self._refresh_video_mode_badge()

        source_type_label = source_type or "-"
        if hasattr(self, "video_placeholder") and self.video_widget is None:
            suffix = " (REC)" if is_recording else ""
            self.video_placeholder.setText(f"Video: {source_type_label}{suffix}")

    def set_video_time(self, seconds: float | None):
        """Aggiorna il timestamp video corrente usato per gli eventi."""
        try:
            self.video_timestamp_seconds = (
                None if seconds is None else max(0.0, float(seconds))
            )
        except Exception:
            self.video_timestamp_seconds = None

        if (
            hasattr(self, "video_placeholder")
            and self.video_widget is None
            and self.video_timestamp_seconds is not None
        ):
            self.video_placeholder.setText(
                f"Video: {self._format_seconds(int(self.video_timestamp_seconds))}"
            )

        if self.video_timestamp_seconds is not None and self.current_context:
            self._resume_video_seconds = self.video_timestamp_seconds
            if self.sync_timer_with_video:
                self.elapsed_seconds_exact = float(self.video_timestamp_seconds)
                self.elapsed_seconds = int(max(0.0, self.elapsed_seconds_exact))
                self.timer_label.setText(self._format_elapsed())

            whole_second = int(self.video_timestamp_seconds)
            if whole_second != self._last_saved_video_second:
                self._save_video_resume_seconds(self.video_timestamp_seconds)
                self._last_saved_video_second = whole_second

        self._highlight_history_by_current_time()

    def _event_video_timestamp(self) -> float:
        """Timestamp evento: preferisce il tempo video, fallback sul timer set."""
        base_time = (
            self.video_timestamp_seconds
            if self.video_timestamp_seconds is not None
            else float(self.elapsed_seconds)
        )

        offset = 0.0
        try:
            offset = float(
                self.current_context.get("video_offset_seconds", 0.0)
                if self.current_context
                else 0.0
            )
        except Exception:
            offset = 0.0

        return max(0.0, base_time + offset)

    def _reset_code_input_feedback_style(self):
        if hasattr(self, "code_input"):
            self.code_input.setStyleSheet("")

    def _feedback_code_submission(self, success: bool, message: str | None = None):
        if hasattr(self, "code_input"):
            border_color = "#16A34A" if success else "#DC2626"
            self.code_input.setStyleSheet(
                f"border: 2px solid {border_color}; border-radius: 6px; padding: 4px;"
            )
            QTimer.singleShot(260, self._reset_code_input_feedback_style)

        if message:
            self.subtitle.setText(message)

        QApplication.beep()
        if not success:
            QTimer.singleShot(120, QApplication.beep)

    def _team_context(self, side: str) -> dict:
        key = "home_team" if side == "home" else "away_team"
        return self.current_context.get(key, {}) if self.current_context else {}

    def _resolve_player_id(
        self, side: str, player_number: str | int | None
    ) -> int | None:
        if player_number is None:
            return None

        team_data = self._team_context(side)
        number_map = team_data.get("number_to_player_id", {})
        if not isinstance(number_map, dict) or not number_map:
            return None

        raw = str(player_number).strip()
        if not raw:
            return None

        candidates = [raw]
        try:
            as_int = int(raw)
            candidates.append(str(as_int))
            candidates.append(str(as_int).zfill(2))
        except Exception:
            pass

        for key in candidates:
            if key in number_map:
                try:
                    return int(number_map[key])
                except Exception:
                    return None
        return None

    def _clear_player_highlight(self):
        if hasattr(self, "home_court"):
            self.home_court.clear_highlight_player()
        if hasattr(self, "away_court"):
            self.away_court.clear_highlight_player()

    def _highlight_player_on_courts(self, side: str, player_number: str | None):
        self._clear_player_highlight()
        if not player_number:
            return

        if side == "home" and hasattr(self, "home_court"):
            self.home_court.set_highlight_player(player_number)
        elif side == "away" and hasattr(self, "away_court"):
            self.away_court.set_highlight_player(player_number)

    def _infer_code_team_side(self, raw_code: str) -> str | None:
        normalized = str(raw_code or "").strip().lower()
        if not normalized:
            return None

        lead = normalized[0]
        second = normalized[1] if len(normalized) > 1 else ""

        if lead == "*":
            return "home"
        if lead == "a" and (second.isdigit() or second == "p"):
            return "home"
        if lead == "b" and (second.isdigit() or second == "p"):
            return "away"
        return None

    def _parse_datavolley_code(self, raw_code: str) -> dict:
        normalized = str(raw_code or "").strip().upper().replace(" ", "")
        if not normalized:
            return {"valid": False, "error": "Codice vuoto"}

        guessed_team = self._infer_code_team_side(normalized)
        team_side = guessed_team or self._selected_code_team_side()

        scan_code = normalized
        if scan_code and scan_code[0] == "*":
            scan_code = scan_code[1:]
        elif (
            len(scan_code) > 1
            and scan_code[0] in {"A", "B"}
            and (scan_code[1].isdigit() or scan_code[1] == "P")
        ):
            scan_code = scan_code[1:]

        if not scan_code:
            return {"valid": False, "error": "Codice incompleto"}

        skill_index = None
        skill = None
        for idx, ch in enumerate(scan_code):
            if ch in self.DATA_VOLLEY_SKILL_ALIASES:
                skill_index = idx
                skill = self.DATA_VOLLEY_SKILL_ALIASES[ch]
                break

        if skill_index is None or skill is None:
            return {
                "valid": False,
                "error": "Skill DataVolley non trovata (usa S/R/E/A/B/D/F)",
            }

        prefix_part = scan_code[:skill_index]
        suffix_part = scan_code[skill_index + 1 :]

        player_number = None
        player_match = re.search(r"(\d{1,2})$", prefix_part)
        if player_match:
            player_number = player_match.group(1).zfill(2)

        evaluation = None
        if suffix_part and suffix_part[0] in self.DATA_VOLLEY_EVALUATIONS:
            evaluation = suffix_part[0]
            suffix_part = suffix_part[1:]

        zone_start = None
        zone_end = None
        extra_part = suffix_part
        zone_pair_match = re.search(r"([1-9])([1-9])$", suffix_part)
        if zone_pair_match:
            zone_start = zone_pair_match.group(1)
            zone_end = zone_pair_match.group(2)
            extra_part = suffix_part[:-2]

        extra_part = extra_part.strip()
        attack_combo = None
        set_code = None
        if extra_part:
            extra_match = re.search(r"([A-Z0-9]{1,2})$", extra_part)
            if extra_match:
                if skill == "A":
                    attack_combo = extra_match.group(1)
                elif skill == "E":
                    set_code = extra_match.group(1)

        return {
            "valid": True,
            "raw": normalized,
            "team_side": team_side,
            "player_number": player_number,
            "skill": skill,
            "evaluation": evaluation,
            "zone_start": zone_start,
            "zone_end": zone_end,
            "attack_combo": attack_combo,
            "set_code": set_code,
        }

    def _resolve_point_team_from_evaluation(
        self,
        side: str,
        skill: str | None,
        evaluation: str | None,
    ) -> str | None:
        eval_token = str(evaluation or "").strip()
        if not eval_token:
            return None

        skill_token = str(skill or "").strip().upper()
        if skill_token not in self.DATA_VOLLEY_SKILL_ALIASES:
            skill_token = "*"

        key_specific = f"{skill_token}{eval_token}"
        key_fallback = f"*{eval_token}"
        outcome = self.point_outcome_map.get(key_specific)
        if outcome is None:
            outcome = self.point_outcome_map.get(key_fallback)

        outcome = str(outcome or "none").strip().lower()
        if outcome == "self":
            return side
        if outcome == "opponent":
            return "away" if side == "home" else "home"
        return None

    def _apply_point_logic(self, side: str) -> dict:
        score_key = "score_home" if side == "home" else "score_away"
        self.current_context[score_key] = self.current_context.get(score_key, 0) + 1

        sideout = side != self.serving_side
        if sideout:
            self._rotate_team_lineup(side)
            self._apply_serving_side(side)
            self.subtitle.setText(
                "Side-out: cambio palla e rotazione automatica applicata."
            )
        else:
            self.subtitle.setText(
                "Punto diretto: mantiene la battuta la stessa squadra."
            )

        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )

        return {
            "side": side,
            "team_name": team_name,
            "sideout": sideout,
            "score_home": int(self.current_context.get("score_home", 0)),
            "score_away": int(self.current_context.get("score_away", 0)),
        }

    def _register_datavolley_code(self):
        if not self.current_context:
            return

        if not self._require_initial_service_selected():
            return

        raw_code = self.code_input.text().strip() if hasattr(self, "code_input") else ""
        if not raw_code:
            return

        parsed = self._parse_datavolley_code(raw_code)
        if not parsed.get("valid"):
            QMessageBox.warning(
                self,
                "Codice DataVolley non valido",
                str(parsed.get("error") or "Formato non riconosciuto"),
            )
            self._feedback_code_submission(False, "Codice non valido")
            if hasattr(self, "code_input"):
                self.code_input.setFocus()
            return

        side = parsed.get("team_side", "home")
        self._highlight_player_on_courts(side, parsed.get("player_number"))

        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )

        skill = parsed.get("skill")
        evaluation = parsed.get("evaluation")
        point_side = self._resolve_point_team_from_evaluation(side, skill, evaluation)

        snapshot = None
        point_result = None
        if point_side is not None:
            snapshot = self._snapshot_state()
            point_result = self._apply_point_logic(point_side)

        history_kind = (
            self.HISTORY_KIND_POINT
            if point_side is not None
            else self.HISTORY_KIND_SKILL
        )

        note_parts = [f"Codice DV: {raw_code}"]
        if parsed.get("player_number"):
            note_parts.append(f"Giocatore #{parsed['player_number']}")
        if point_result is not None:
            note_parts.append(
                f"Punto {point_result['team_name']} ({'side-out' if point_result['sideout'] else 'punto diretto'})"
            )

        player_id = self._resolve_player_id(side, parsed.get("player_number"))

        event_id = self._persist_event(
            team_side=side,
            player_id=player_id,
            skill=skill,
            evaluation=evaluation,
            notes=" | ".join(note_parts),
            kind=history_kind,
            zone_start=parsed.get("zone_start"),
            zone_end=parsed.get("zone_end"),
            attack_combo=parsed.get("attack_combo"),
            set_code=parsed.get("set_code"),
        )

        if snapshot is not None:
            self.rally_history.append({"snapshot": snapshot, "event_id": event_id})

        history_text = f"{self._format_elapsed()} | {team_name} | {raw_code}"
        if point_result is not None:
            history_text = f"{history_text} -> {point_result['score_home']}-{point_result['score_away']}"

        self._append_history(
            history_text,
            event_id=event_id,
            kind=history_kind,
        )

        self._refresh_view()
        self._feedback_code_submission(
            True,
            f"Codice registrato: {raw_code}",
        )

        self.code_input.clear()
        self.code_input.setFocus()

        if hasattr(self, "btn_toggle_keypad") and self.btn_toggle_keypad.isChecked():
            self.btn_toggle_keypad.setChecked(False)

    def _is_editing_completed_match(self) -> bool:
        if not self.current_context:
            return False
        return bool(self.current_context.get("editing_completed_match", False))

    def _set_controls_enabled(self, enabled: bool):
        self.btn_point_home.setEnabled(enabled)
        self.btn_point_away.setEnabled(enabled)
        self.btn_undo.setEnabled(enabled)
        self.btn_finish_set.setEnabled(enabled)
        self.btn_finish_match.setEnabled(
            enabled and not self._is_editing_completed_match()
        )
        self.btn_set_actions.setEnabled(enabled)
        self.home_court.setEnabled(enabled)
        self.away_court.setEnabled(enabled)
        self.btn_timer_toggle.setEnabled(enabled)
        self.btn_timer_reset.setEnabled(enabled)
        if hasattr(self, "btn_pause_video_scout"):
            can_pause_video = (
                enabled
                and self.video_widget is not None
                and not self.video_is_live
                and hasattr(self.video_widget, "set_paused")
            )
            self.btn_pause_video_scout.setEnabled(can_pause_video)
            if not can_pause_video and self.btn_pause_video_scout.isChecked():
                self.btn_pause_video_scout.blockSignals(True)
                self.btn_pause_video_scout.setChecked(False)
                self.btn_pause_video_scout.blockSignals(False)
        if hasattr(self, "btn_position_reception"):
            self.btn_position_reception.setEnabled(enabled)

        if hasattr(self, "code_team_selector"):
            self.code_team_selector.setEnabled(enabled)
        if hasattr(self, "code_input"):
            self.code_input.setEnabled(enabled)
        if hasattr(self, "btn_send_code"):
            self.btn_send_code.setEnabled(enabled)
        if hasattr(self, "btn_clear_code"):
            self.btn_clear_code.setEnabled(enabled)
        if hasattr(self, "btn_config_shortcuts"):
            self.btn_config_shortcuts.setEnabled(True)
        if hasattr(self, "btn_reset_shortcuts"):
            self.btn_reset_shortcuts.setEnabled(True)
        if hasattr(self, "keypad_size_selector"):
            self.keypad_size_selector.setEnabled(True)
        if hasattr(self, "keyboard_mode_selector"):
            self.keyboard_mode_selector.setEnabled(True)
        if hasattr(self, "btn_config_hotkeys"):
            self.btn_config_hotkeys.setEnabled(True)
        if hasattr(self, "btn_reset_hotkeys"):
            self.btn_reset_hotkeys.setEnabled(True)
        if hasattr(self, "btn_toggle_keypad"):
            self.btn_toggle_keypad.setEnabled(enabled and not self.keyboard_only_mode)
            if not enabled and self.btn_toggle_keypad.isChecked():
                self.btn_toggle_keypad.setChecked(False)

        if hasattr(self, "btn_initial_service_home"):
            self.btn_initial_service_home.setEnabled(
                enabled and not self.initial_service_selected
            )
        if hasattr(self, "btn_initial_service_away"):
            self.btn_initial_service_away.setEnabled(
                enabled and not self.initial_service_selected
            )
        if hasattr(self, "btn_back_to_scouts"):
            self.btn_back_to_scouts.setEnabled(True)

        for btn in self.skill_buttons:
            btn.setEnabled(enabled)
        for btn in self.code_shortcut_buttons:
            btn.setEnabled(enabled)
        for btn in self.code_keypad_buttons:
            btn.setEnabled(enabled)

    def _timeout_limit_per_set(self) -> int:
        try:
            return max(
                1, int(self.current_context.get("timeout_limit_per_set", 2) or 2)
            )
        except Exception:
            return 2

    def _update_timeout_labels(self):
        limit = self._timeout_limit_per_set()
        self.timeout_home_label.setText(
            f"TO Casa: {self.timeouts_used.get('home', 0)}/{limit}"
        )
        self.timeout_away_label.setText(
            f"TO Ospiti: {self.timeouts_used.get('away', 0)}/{limit}"
        )

    def _format_seconds(self, total_seconds: int) -> str:
        minutes = max(0, int(total_seconds)) // 60
        seconds = max(0, int(total_seconds)) % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _format_elapsed(self) -> str:
        return self._format_seconds(int(max(0.0, float(self.elapsed_seconds_exact))))

    def _reset_timer_ui(self):
        self.timer_label.setText(self._format_elapsed())
        self.btn_timer_toggle.setText("Avvia timer")

    def _on_timer_tick(self):
        self.elapsed_seconds_exact = max(0.0, float(self.elapsed_seconds_exact) + 1.0)
        self.elapsed_seconds = int(self.elapsed_seconds_exact)
        self.timer_label.setText(self._format_elapsed())
        self._highlight_history_by_current_time()

    def _toggle_timer(self):
        if self.timer_running:
            self.timer.stop()
            self.timer_running = False
            self.btn_timer_toggle.setText("Avvia timer")
        else:
            self.timer.start()
            self.timer_running = True
            self.btn_timer_toggle.setText("Pausa timer")

    def _reset_timer(self):
        self.elapsed_seconds_exact = 0.0
        self.elapsed_seconds = 0
        self.timer_label.setText(self._format_elapsed())
        self._highlight_history_by_current_time()

    def _normalize_lineup_number(self, value) -> str | None:
        if value is None:
            return None
        raw = str(value).strip()
        if not raw or raw == "-":
            return None
        try:
            return str(int(raw))
        except Exception:
            return raw.lstrip("0") or raw

    def _find_player_position_in_lineup(
        self, side: str, player_number: str | int | None
    ) -> str | None:
        target = self._normalize_lineup_number(player_number)
        if target is None:
            return None

        lineup = self._team_context(side).get("lineup", {})
        for pos in ("P1", "P2", "P3", "P4", "P5", "P6"):
            if self._normalize_lineup_number(lineup.get(pos)) == target:
                return pos
        return None

    def _detect_setter_number_for_side(self, side: str) -> str | None:
        team_data = self._team_context(side)
        lineup = team_data.get("lineup", {})
        lineup_numbers = {
            self._normalize_lineup_number(v)
            for v in lineup.values()
            if self._normalize_lineup_number(v) is not None
        }
        if not lineup_numbers:
            return None

        explicit = self._normalize_lineup_number(team_data.get("setter_number"))
        if explicit in lineup_numbers:
            return explicit

        if self.db is None or not self.current_context:
            return None

        match_id = self.current_context.get("match_id")
        team_id = team_data.get("id")
        if match_id is None or team_id is None:
            return None

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchPlayer

                rows = (
                    session.query(MatchPlayer)
                    .filter_by(match_id=match_id, team_id=team_id)
                    .all()
                )

                starters = [r for r in rows if bool(getattr(r, "is_starter", False))]
                ordered_sets = [starters, rows]
                for source_rows in ordered_sets:
                    for row in source_rows:
                        role_text = str(getattr(row, "role", "") or "").strip().lower()
                        if "palleggiatore" not in role_text:
                            continue
                        number = self._normalize_lineup_number(
                            getattr(row, "number", None)
                        )
                        if number in lineup_numbers:
                            return number
        except Exception:
            return None

        return None

    def _refresh_setter_numbers(self):
        self.setter_number_by_side["home"] = self._detect_setter_number_for_side("home")
        self.setter_number_by_side["away"] = self._detect_setter_number_for_side("away")

    def _update_outer_service_hints(self):
        entries = {
            "home": getattr(self, "home_outer_status", None),
            "away": getattr(self, "away_outer_status", None),
        }
        for side, label in entries.items():
            if label is None:
                continue

            is_serving = side == self.serving_side
            status = "BATTUTA" if is_serving else "RICEZIONE"
            rotation_hint = self.reception_rotation_hint.get(side) or "-"
            label.setText(f"{status}\n{rotation_hint}")

            if is_serving:
                label.setStyleSheet(
                    "font-size: 11px; font-weight: bold; color: white;"
                    "border: 1px solid #C2410C; border-radius: 8px; padding: 6px 4px;"
                    "background-color: #E95420;"
                )
            else:
                label.setStyleSheet(
                    "font-size: 11px; font-weight: bold; color: #F6EFE9;"
                    "border: 1px solid #374151; border-radius: 8px; padding: 6px 4px;"
                    "background-color: #4B5563;"
                )

    def _update_initial_service_controls(self):
        if not hasattr(self, "initial_service_status"):
            return

        enabled = bool(self.current_context)
        lock_selection = self.initial_service_selected

        if hasattr(self, "btn_initial_service_home"):
            self.btn_initial_service_home.setEnabled(enabled and not lock_selection)
        if hasattr(self, "btn_initial_service_away"):
            self.btn_initial_service_away.setEnabled(enabled and not lock_selection)

        if not enabled:
            self.initial_service_status.setText("Seleziona chi batte ad inizio set")
        elif lock_selection:
            team_name = (
                self.current_context.get("home_team", {}).get("name", "Casa")
                if self.serving_side == "home"
                else self.current_context.get("away_team", {}).get("name", "Ospiti")
            )
            self.initial_service_status.setText(
                f"Battuta iniziale impostata: {team_name}"
            )
        else:
            self.initial_service_status.setText("Seleziona chi batte ad inizio set")

    def _set_initial_service(self, side: str):
        if not self.current_context or self.initial_service_selected:
            return

        self.initial_service_selected = True
        self._apply_serving_side(side)
        self._update_initial_service_controls()

        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if self.serving_side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )
        note = f"Battuta iniziale set: {team_name}"
        self.subtitle.setText(note)

        event_id = self._persist_event(
            team_side=self.serving_side,
            skill="S",
            notes=note,
            kind=self.HISTORY_KIND_SYSTEM,
        )
        self._append_history(
            f"{self._format_elapsed()} | {note}",
            event_id=event_id,
            kind=self.HISTORY_KIND_SYSTEM,
        )

        self._refresh_view()

    def _require_initial_service_selected(self) -> bool:
        if self.initial_service_selected:
            return True

        QMessageBox.information(
            self,
            "Battuta iniziale non impostata",
            "Seleziona prima la squadra al servizio a inizio set.",
        )
        return False

    def _lineup_numbers_for_side(self, side: str) -> list[str]:
        lineup = self._team_context(side).get("lineup", {})
        ordered = []
        for pos in ("P1", "P2", "P3", "P4", "P5", "P6"):
            normalized = self._normalize_lineup_number(lineup.get(pos))
            if normalized and normalized not in ordered:
                ordered.append(normalized)
        return ordered

    def _position_reception_with_prompt(self):
        if not self.current_context:
            return

        options = ["Auto (squadra in ricezione)", "Casa", "Ospiti"]
        selected, ok = QInputDialog.getItem(
            self,
            "Posizionamento ricezione",
            "Seleziona la squadra da posizionare in ricezione:",
            options,
            0,
            False,
        )
        if not ok:
            return

        if selected == "Casa":
            side = "home"
        elif selected == "Ospiti":
            side = "away"
        else:
            if not self._require_initial_service_selected():
                return
            side = "away" if self.serving_side == "home" else "home"

        side = "away" if side == "away" else "home"
        players = self._lineup_numbers_for_side(side)
        if not players:
            QMessageBox.warning(
                self,
                "Formazione non disponibile",
                "Non ci sono giocatori in campo da posizionare.",
            )
            return

        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )
        existing_positions = self.reception_manual_positions.get(side, {})
        lineup_positions = self._team_context(side).get("lineup", {})

        dialog = ReceptionPositionDialog(
            team_name=team_name,
            team_side=side,
            players=players,
            initial_positions=existing_positions,
            lineup_positions=lineup_positions,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        placed_positions = dialog.positions()
        self.reception_manual_positions[side] = dict(placed_positions)
        self._save_reception_positions_for_side(
            side, self.reception_manual_positions[side]
        )
        if self.current_context is not None:
            self.current_context["reception_manual_positions"] = {
                "home": dict(self.reception_manual_positions.get("home", {})),
                "away": dict(self.reception_manual_positions.get("away", {})),
            }

        placed_count = len(placed_positions)
        self.reception_rotation_hint[side] = f"Rx manuale ({placed_count})"

        note = f"Posizionata ricezione {team_name}: {placed_count} giocatori posizionati manualmente"
        self.subtitle.setText(note)

        event_id = self._persist_event(
            team_side=side,
            skill="R",
            notes=note,
            kind=self.HISTORY_KIND_SYSTEM,
        )
        self._append_history(
            f"{self._format_elapsed()} | {note}",
            event_id=event_id,
            kind=self.HISTORY_KIND_SYSTEM,
        )

        self._update_outer_service_hints()

    def _resolve_serving_side(self, context: dict) -> str:
        away_id = context.get("away_team", {}).get("id")
        serving_team_id = context.get("serving_team_id")

        if serving_team_id is not None and serving_team_id == away_id:
            return "away"
        return "home"

    def _apply_serving_side(self, side: str):
        self.serving_side = "away" if side == "away" else "home"

        if self.current_context:
            if self.serving_side == "away":
                self.current_context["serving_team_id"] = self.current_context.get(
                    "away_team", {}
                ).get("id")
            else:
                self.current_context["serving_team_id"] = self.current_context.get(
                    "home_team", {}
                ).get("id")

        self._set_code_team_side(self.serving_side)
        self._update_outer_service_hints()

    def _rotate_team_lineup(self, side: str):
        """Ruota la lineup usando la utility condivisa core."""
        if not self.current_context:
            return

        team_key = "home_team" if side == "home" else "away_team"
        team_data = self.current_context.get(team_key, {})
        team_data["lineup"] = rotate_lineup_clockwise(team_data.get("lineup", {}))

    def _snapshot_state(self) -> dict:
        return {
            "score_home": self.current_context.get("score_home", 0),
            "score_away": self.current_context.get("score_away", 0),
            "serving_side": self.serving_side,
            "home_lineup": deepcopy(
                self.current_context.get("home_team", {}).get("lineup", {})
            ),
            "away_lineup": deepcopy(
                self.current_context.get("away_team", {}).get("lineup", {})
            ),
            "subtitle": self.subtitle.text(),
        }

    def _restore_state(self, snapshot: dict):
        self.current_context["score_home"] = snapshot.get("score_home", 0)
        self.current_context["score_away"] = snapshot.get("score_away", 0)

        self.current_context.setdefault("home_team", {})["lineup"] = snapshot.get(
            "home_lineup", {}
        )
        self.current_context.setdefault("away_team", {})["lineup"] = snapshot.get(
            "away_lineup", {}
        )

        self._apply_serving_side(snapshot.get("serving_side", "home"))
        self.subtitle.setText(snapshot.get("subtitle", self.subtitle.text()))
        self._refresh_view()

    def _ensure_set_record(self, session):
        """Garantisce l'esistenza del set corrente nel DB e ritorna il record."""
        if self.db is None or not self.current_context:
            return None

        from volleyball_scout.core.models import MatchSet

        match_id = self.current_context.get("match_id")
        set_number = int(self.current_context.get("set_number", 1) or 1)
        if match_id is None:
            return None

        set_record = (
            session.query(MatchSet)
            .filter_by(match_id=match_id, set_number=set_number)
            .first()
        )
        if set_record is None:
            set_record = MatchSet(
                match_id=match_id,
                set_number=set_number,
                score_home=int(self.current_context.get("score_home", 0) or 0),
                score_away=int(self.current_context.get("score_away", 0) or 0),
            )
            session.add(set_record)
            session.flush()

        self.current_set_id = set_record.id
        return set_record

    def _persist_event(
        self,
        team_side: str | None = None,
        player_id: int | None = None,
        skill: str | None = None,
        evaluation: str | None = None,
        notes: str = "",
        kind: str = "SY",
        zone_start: str | None = None,
        zone_end: str | None = None,
        attack_combo: str | None = None,
        set_code: str | None = None,
        video_timestamp_override: float | None = None,
    ) -> int | None:
        """Salva un evento di scouting nel DB."""
        if self.db is None or not self.current_context:
            return None

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import ScoutEvent

                set_record = self._ensure_set_record(session)

                next_counter = self.event_counter + 1
                team_code = None
                if team_side == "home":
                    team_code = "a"
                elif team_side == "away":
                    team_code = "b"

                event_timestamp = (
                    self._event_video_timestamp()
                    if video_timestamp_override is None
                    else max(0.0, float(video_timestamp_override))
                )

                event = ScoutEvent(
                    match_id=self.current_context.get("match_id"),
                    set_id=set_record.id if set_record is not None else None,
                    player_id=player_id,
                    team_side=team_code,
                    skill=skill,
                    evaluation=evaluation,
                    zone_start=zone_start,
                    zone_end=zone_end,
                    attack_combo=attack_combo,
                    set_code=set_code,
                    score_home=int(self.current_context.get("score_home", 0) or 0),
                    score_away=int(self.current_context.get("score_away", 0) or 0),
                    rally_number=next_counter,
                    video_timestamp=event_timestamp,
                    notes=notes,
                    special_code=self._normalize_history_kind(kind),
                )
                session.add(event)
                session.flush()

                self.event_counter = next_counter
                return int(event.id)

        except Exception as e:
            print(f"⚠️ Errore salvataggio evento scouting: {e}")
            return None

    def _delete_event(self, event_id: int | None):
        """Elimina un evento dal DB (usato per undo)."""
        if self.db is None or event_id is None:
            return

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import ScoutEvent

                event = session.query(ScoutEvent).filter_by(id=event_id).first()
                if event is not None:
                    session.delete(event)
        except Exception as e:
            print(f"⚠️ Errore delete evento scouting: {e}")

    def _normalize_history_kind(self, kind: str | None) -> str:
        kind_upper = str(kind or self.HISTORY_KIND_SYSTEM).upper()
        if kind_upper in {
            self.HISTORY_KIND_POINT,
            self.HISTORY_KIND_SKILL,
            self.HISTORY_KIND_SYSTEM,
        }:
            return kind_upper
        return self.HISTORY_KIND_SYSTEM

    def _matches_history_filter(self, kind: str) -> bool:
        selected = (
            self.history_filter.currentText()
            if hasattr(self, "history_filter")
            else "Tutti"
        )
        if selected == "Punti":
            return kind == self.HISTORY_KIND_POINT
        if selected == "Skill":
            return kind == self.HISTORY_KIND_SKILL
        if selected == "Sistema":
            return kind == self.HISTORY_KIND_SYSTEM
        return True

    def _extract_note_from_history_text(self, text: str) -> str:
        parts = str(text or "").split("|", 1)
        if len(parts) == 2:
            return parts[1].strip()
        return str(text or "").strip()

    def _timestamp_from_history_text(self, text: str) -> float | None:
        match = re.match(r"^\s*(\d+):([0-5]\d)\s*\|", str(text or ""))
        if not match:
            return None
        try:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return float(max(0, minutes * 60 + seconds))
        except Exception:
            return None

    def _compose_history_text(self, note: str, timestamp_seconds: float | None) -> str:
        if timestamp_seconds is None:
            return str(note or "")
        return (
            f"{self._format_seconds(int(max(0.0, float(timestamp_seconds))))} | "
            f"{str(note or '').strip()}"
        )

    def _history_timestamp_from_record(self, record: dict) -> float | None:
        value = record.get("timestamp_seconds")
        if value is not None:
            try:
                return float(max(0.0, float(value)))
            except Exception:
                pass
        return self._timestamp_from_history_text(record.get("text", ""))

    def _set_record_timestamp(self, record: dict, timestamp_seconds: float):
        ts = float(max(0.0, float(timestamp_seconds)))
        note = self._extract_note_from_history_text(record.get("text", ""))
        record["timestamp_seconds"] = ts
        record["text"] = self._compose_history_text(note, ts)

    def _current_reference_seconds(self) -> float:
        if self.video_timestamp_seconds is not None:
            try:
                return float(max(0.0, float(self.video_timestamp_seconds)))
            except Exception:
                pass
        return float(max(0.0, float(self.elapsed_seconds_exact)))

    def _event_item_timestamp(self, item: QListWidgetItem | None) -> float | None:
        if item is None:
            return None

        raw = item.data(self.history_timestamp_role)
        if raw is not None:
            try:
                return float(max(0.0, float(raw)))
            except Exception:
                pass

        return self._timestamp_from_history_text(item.text())

    def _find_history_record_index_by_event_id(self, event_id: int | None) -> int:
        if event_id is None:
            return -1

        for idx, record in enumerate(self.history_records):
            if record.get("event_id") == event_id:
                return idx
        return -1

    def _highlight_history_by_current_time(self, scroll_to_active: bool = True):
        if not hasattr(self, "events_list"):
            return

        list_count = self.events_list.count()
        if list_count <= 0:
            self.active_history_event_id = None
            return

        reference_seconds = self._current_reference_seconds()
        best_row = -1
        best_ts = -1.0

        for row in range(list_count):
            item = self.events_list.item(row)
            if item is None:
                continue

            ts = self._event_item_timestamp(item)
            if ts is None:
                continue

            item.setData(self.history_timestamp_role, float(ts))
            if ts <= (reference_seconds + 0.35) and ts >= best_ts:
                best_row = row
                best_ts = ts

        if best_row < 0:
            best_row = 0

        previous_event_id = self.active_history_event_id
        active_item = None

        for row in range(list_count):
            item = self.events_list.item(row)
            if item is None:
                continue

            row_font = item.font()
            if row == best_row:
                active_item = item
                item.setBackground(QColor("#F59E0B"))
                item.setForeground(QColor("#111827"))
                row_font.setBold(True)
            else:
                item.setBackground(QColor(0, 0, 0, 0))
                item.setForeground(QColor("#E5E7EB"))
                row_font.setBold(False)
            item.setFont(row_font)

        if active_item is None:
            self.active_history_event_id = None
            return

        current_event_id = active_item.data(Qt.ItemDataRole.UserRole)
        self.active_history_event_id = (
            int(current_event_id) if current_event_id is not None else None
        )

        if (
            scroll_to_active
            and self.active_history_event_id is not None
            and self.active_history_event_id != previous_event_id
        ):
            self.events_list.scrollToItem(
                active_item,
                QListWidget.ScrollHint.PositionAtCenter,
            )

    def _seek_video_to_timestamp(self, seconds: float | None):
        if seconds is None or self.video_widget is None:
            return

        target = max(0.0, float(seconds))
        try:
            if hasattr(self.video_widget, "seek_to"):
                self.video_widget.seek_to(target)
            elif hasattr(self.video_widget, "set_resume_position"):
                self.video_widget.set_resume_position(target)
        except Exception:
            pass

    def _on_event_item_double_clicked(self, item: QListWidgetItem):
        self._seek_video_to_timestamp(self._event_item_timestamp(item))

    def _event_timestamp_for_event_id(self, event_id: int | None) -> float | None:
        if event_id is None:
            return None

        for record in self.history_records:
            if record.get("event_id") == event_id:
                return self._history_timestamp_from_record(record)
        return None

    def _nudge_event_timestamp(self, event_id: int | None, delta_seconds: float):
        base = self._event_timestamp_for_event_id(event_id)
        if base is None:
            base = self._current_reference_seconds()
        self._update_event_timestamp(
            event_id, max(0.0, float(base) + float(delta_seconds))
        )

    def _update_event_timestamp(self, event_id: int | None, new_seconds: float):
        if event_id is None:
            return

        target = float(max(0.0, float(new_seconds)))

        if self.db is not None:
            try:
                with self.db.session_scope() as session:
                    from volleyball_scout.core.models import ScoutEvent

                    row = session.query(ScoutEvent).filter_by(id=int(event_id)).first()
                    if row is not None:
                        row.video_timestamp = target
            except Exception as e:
                print(f"⚠️ Errore update timestamp evento: {e}")

        for record in self.history_records:
            if record.get("event_id") == event_id:
                self._set_record_timestamp(record, target)
                break

        self._apply_history_filter()
        self._highlight_history_by_current_time(scroll_to_active=False)

    def _insert_code_before_event(self, item: QListWidgetItem):
        if not self.current_context:
            return

        before_event_id = item.data(Qt.ItemDataRole.UserRole)
        before_ts = self._event_item_timestamp(item)
        if before_ts is None:
            before_ts = self._current_reference_seconds()

        raw_code, ok = QInputDialog.getText(
            self,
            "Aggiungi codice prima",
            "Codice DataVolley da inserire prima dell'evento selezionato:",
        )
        if not ok:
            return

        raw_code = str(raw_code or "").strip()
        if not raw_code:
            return

        parsed = self._parse_datavolley_code(raw_code)
        if not parsed.get("valid"):
            QMessageBox.warning(
                self,
                "Codice DataVolley non valido",
                str(parsed.get("error") or "Formato non riconosciuto"),
            )
            return

        side = parsed.get("team_side", "home")
        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )

        insert_ts = max(0.0, float(before_ts) - 0.05)
        player_id = self._resolve_player_id(side, parsed.get("player_number"))

        note = f"Codice DV (inserito): {raw_code}"
        event_id = self._persist_event(
            team_side=side,
            player_id=player_id,
            skill=parsed.get("skill"),
            evaluation=parsed.get("evaluation"),
            notes=note,
            kind=self.HISTORY_KIND_SKILL,
            zone_start=parsed.get("zone_start"),
            zone_end=parsed.get("zone_end"),
            attack_combo=parsed.get("attack_combo"),
            set_code=parsed.get("set_code"),
            video_timestamp_override=insert_ts,
        )

        history_text = f"{team_name} | {raw_code}"
        self._append_history(
            history_text,
            event_id=event_id,
            kind=self.HISTORY_KIND_SKILL,
            timestamp_seconds=insert_ts,
            insert_before_event_id=before_event_id,
        )

        self.subtitle.setText(f"Inserito codice prima: {raw_code}")

    def _open_events_context_menu(self, pos):
        item = self.events_list.itemAt(pos)
        if item is None:
            return

        menu = QMenu(self)

        ts = self._event_item_timestamp(item)
        if ts is not None:
            goto_action = menu.addAction("Vai al tempo evento")
            goto_action.triggered.connect(
                lambda: self._seek_video_to_timestamp(float(ts))
            )

        event_id = item.data(Qt.ItemDataRole.UserRole)
        if event_id is not None:
            align_action = menu.addAction("Allinea evento al tempo video corrente")
            align_action.triggered.connect(
                lambda eid=int(event_id): self._update_event_timestamp(
                    eid, self._current_reference_seconds()
                )
            )

            nudge_back_action = menu.addAction("Sposta evento -1s")
            nudge_back_action.triggered.connect(
                lambda eid=int(event_id): self._nudge_event_timestamp(eid, -1.0)
            )

            nudge_forward_action = menu.addAction("Sposta evento +1s")
            nudge_forward_action.triggered.connect(
                lambda eid=int(event_id): self._nudge_event_timestamp(eid, 1.0)
            )

            menu.addSeparator()
            add_before_action = menu.addAction("Aggiungi codice prima")
            add_before_action.triggered.connect(
                lambda: self._insert_code_before_event(item)
            )

        menu.exec(self.events_list.viewport().mapToGlobal(pos))

    def _apply_history_filter(self, _value=None):
        self.events_list.clear()
        for record in self.history_records:
            kind = self._normalize_history_kind(record.get("kind"))
            if not self._matches_history_filter(kind):
                continue

            item = QListWidgetItem(record.get("text", ""))
            event_id = record.get("event_id")
            if event_id is not None:
                item.setData(Qt.ItemDataRole.UserRole, event_id)

            timestamp = self._history_timestamp_from_record(record)
            if timestamp is not None:
                item.setData(self.history_timestamp_role, float(timestamp))

            self.events_list.addItem(item)

        self.events_list.scrollToBottom()
        self._highlight_history_by_current_time(scroll_to_active=False)

    def _append_history(
        self,
        text: str,
        event_id: int | None = None,
        kind: str = "SY",
        timestamp_seconds: float | None = None,
        insert_before_event_id: int | None = None,
    ):
        normalized_kind = self._normalize_history_kind(kind)
        ts = timestamp_seconds
        if ts is None:
            try:
                ts = self._event_video_timestamp()
            except Exception:
                ts = None

        note = self._extract_note_from_history_text(text)
        final_text = self._compose_history_text(note, ts)

        record = {
            "text": final_text,
            "event_id": event_id,
            "kind": normalized_kind,
            "timestamp_seconds": ts,
        }

        if insert_before_event_id is None:
            self.history_records.append(record)
        else:
            idx = self._find_history_record_index_by_event_id(insert_before_event_id)
            if idx >= 0:
                self.history_records.insert(idx, record)
            else:
                self.history_records.append(record)

        self._apply_history_filter()

    def _remove_history_item_by_event_id(self, event_id: int | None):
        if event_id is None:
            return

        self.history_records = [
            record
            for record in self.history_records
            if record.get("event_id") != event_id
        ]
        self._apply_history_filter()

    def _refresh_view(self):
        if not self.current_context:
            return

        home = self.current_context.get("home_team", {})
        away = self.current_context.get("away_team", {})

        self.home_score.setText(str(self.current_context.get("score_home", 0)))
        self.away_score.setText(str(self.current_context.get("score_away", 0)))
        self.timer_label.setText(self._format_elapsed())
        self._update_timeout_labels()

        self.home_court.update_lineup(
            home.get("name", "Casa"),
            home.get("lineup", {}),
            libero=home.get("libero"),
            serving=self.serving_side == "home",
            setter_number=self.setter_number_by_side.get("home"),
        )
        self.away_court.update_lineup(
            away.get("name", "Trasferta"),
            away.get("lineup", {}),
            libero=away.get("libero"),
            serving=self.serving_side == "away",
            setter_number=self.setter_number_by_side.get("away"),
        )

        self._update_initial_service_controls()
        self._update_outer_service_hints()

    def _register_skill_event(self, skill_name: str):
        if not self.current_context:
            return

        side = self.serving_side
        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )

        skill_code = self.SKILL_CODES.get(skill_name)
        note = f"Evento rapido: {skill_name}"
        event_id = self._persist_event(
            team_side=side,
            skill=skill_code,
            notes=note,
            kind=self.HISTORY_KIND_SKILL,
        )

        self._append_history(
            f"{self._format_elapsed()} | {team_name} - {skill_name}",
            event_id=event_id,
            kind=self.HISTORY_KIND_SKILL,
        )

    def _register_timeout(self, side: str):
        if not self.current_context:
            return

        limit = self._timeout_limit_per_set()
        used = int(self.timeouts_used.get(side, 0) or 0)
        if used >= limit:
            QMessageBox.warning(
                self,
                "Timeout non disponibile",
                f"La squadra ha già usato tutti i timeout disponibili ({limit}).",
            )
            return

        self.timeouts_used[side] = used + 1
        self._update_timeout_labels()

        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )
        note = f"Timeout {team_name} ({self.timeouts_used[side]}/{limit})"
        event_id = self._persist_event(
            team_side=side,
            notes=note,
            kind=self.HISTORY_KIND_SYSTEM,
        )

        self.subtitle.setText(note)
        self._append_history(
            f"{self._format_elapsed()} | {note}",
            event_id=event_id,
            kind=self.HISTORY_KIND_SYSTEM,
        )

    def _register_substitution(self, side: str):
        if not self.current_context:
            return

        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )

        num_out, ok_out = QInputDialog.getText(
            self,
            "Sostituzione",
            f"{team_name}: numero giocatore USCENTE",
        )
        if not ok_out:
            return

        num_in, ok_in = QInputDialog.getText(
            self,
            "Sostituzione",
            f"{team_name}: numero giocatore ENTRANTE",
        )
        if not ok_in:
            return

        num_out = num_out.strip() or "?"
        num_in = num_in.strip() or "?"

        note = f"Sostituzione {team_name}: {num_out} → {num_in}"
        event_id = self._persist_event(
            team_side=side,
            notes=note,
            kind=self.HISTORY_KIND_SYSTEM,
        )
        self.subtitle.setText(note)
        self._append_history(
            f"{self._format_elapsed()} | {note}",
            event_id=event_id,
            kind=self.HISTORY_KIND_SYSTEM,
        )

    def _register_point(self, side: str):
        if not self.current_context:
            return

        if not self._require_initial_service_selected():
            return

        snapshot = self._snapshot_state()
        point_result = self._apply_point_logic(side)

        note = (
            f"Punto {point_result['team_name']} "
            f"({'side-out' if point_result['sideout'] else 'punto diretto'})"
        )
        event_id = self._persist_event(
            team_side=side,
            evaluation="#",
            notes=note,
            kind=self.HISTORY_KIND_POINT,
        )

        self.rally_history.append({"snapshot": snapshot, "event_id": event_id})

        self._append_history(
            f"{self._format_elapsed()} | Punto {point_result['team_name']} -> {point_result['score_home']}-{point_result['score_away']}",
            event_id=event_id,
            kind=self.HISTORY_KIND_POINT,
        )

        self._refresh_view()

    def _undo_last_rally(self):
        if not self.rally_history:
            return

        action = self.rally_history.pop()
        self._restore_state(action["snapshot"])

        event_id = action.get("event_id")
        self._delete_event(event_id)
        self._remove_history_item_by_event_id(event_id)

        self.subtitle.setText("Ultimo rally annullato.")

    def _on_serving_selected(self, side: str):
        if not self.current_context:
            return

        if self.initial_service_selected:
            QMessageBox.information(
                self,
                "Servizio già impostato",
                "La battuta manuale è disponibile solo a inizio set.",
            )
            return

        self._set_initial_service(side)

    def _compute_sets_won(self, session, match_id: int) -> tuple[int, int]:
        """Conta i set vinti per home/away per il match."""
        from volleyball_scout.core.models import MatchSet

        all_sets = session.query(MatchSet).filter_by(match_id=match_id).all()
        home_sets_won = sum(1 for s in all_sets if s.winner == "home")
        away_sets_won = sum(1 for s in all_sets if s.winner == "away")
        return home_sets_won, away_sets_won

    def _resolve_video_path_for_match(self) -> str | None:
        if not self.current_context:
            return None

        current_path = str(self.current_context.get("video_path") or "").strip()
        if current_path:
            return current_path

        source_type = str(self.video_source_info.get("type", "") or "").strip()
        source_value = str(self.video_source_info.get("value", "") or "").strip()
        recorded_path = str(
            self.video_source_info.get("recorded_path", "") or ""
        ).strip()

        if recorded_path:
            return recorded_path
        if source_type == "file" and source_value:
            return source_value
        return None

    def _persist_video_link_on_match_close(self):
        video_path = self._resolve_video_path_for_match()
        if not video_path:
            return

        if self.current_context is not None:
            self.current_context["video_path"] = video_path
        self._persist_current_match_video_path(video_path)

    def _finish_set(self):
        """Chiude il set corrente e richiede la formazione del set successivo."""
        if not self.current_context:
            return

        was_running = self.timer_running
        if self.timer_running:
            self._toggle_timer()

        match_id = self.current_context.get("match_id")
        set_number = int(self.current_context.get("set_number", 1) or 1)
        score_home = int(self.current_context.get("score_home", 0) or 0)
        score_away = int(self.current_context.get("score_away", 0) or 0)

        confirm = QMessageBox.question(
            self,
            "Conferma Fine Set",
            f"Confermi la chiusura del set {set_number}?\n\n"
            f"Punteggio: {score_home}-{score_away}\n"
            f"Durata: {self._format_elapsed()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            if was_running:
                self._toggle_timer()
            return

        winner = None
        if score_home > score_away:
            winner = "home"
        elif score_away > score_home:
            winner = "away"
        else:
            QMessageBox.warning(
                self,
                "Punteggio non valido",
                "Non puoi chiudere un set in parità. Aggiorna il punteggio e riprova.",
            )
            if was_running:
                self._toggle_timer()
            return

        home_sets_won = 0
        away_sets_won = 0
        match_completed = False
        match_winner = None

        if self.db is not None and match_id is not None:
            try:
                with self.db.session_scope() as session:
                    from volleyball_scout.core.models import Match

                    set_record = self._ensure_set_record(session)
                    if set_record is not None:
                        set_record.score_home = score_home
                        set_record.score_away = score_away
                        set_record.duration = int(
                            max(0.0, float(self.elapsed_seconds_exact))
                        )
                        set_record.winner = winner

                    home_sets_won, away_sets_won = self._compute_sets_won(
                        session, match_id
                    )

                    match_completed = home_sets_won >= 3 or away_sets_won >= 3
                    if match_completed:
                        match_winner = (
                            "home" if home_sets_won > away_sets_won else "away"
                        )

                    match_obj = session.query(Match).filter_by(id=match_id).first()
                    if match_obj is not None:
                        match_obj.status = (
                            "completed" if match_completed else "in_progress"
                        )
            except Exception as e:
                print(f"⚠️ Errore chiusura set: {e}")

        end_note = (
            f"Fine set {set_number}: "
            f"{self.current_context.get('home_team', {}).get('name', 'Casa')} {score_home} - "
            f"{self.current_context.get('away_team', {}).get('name', 'Ospiti')} {score_away}"
        )
        end_event_id = self._persist_event(
            notes=end_note,
            kind=self.HISTORY_KIND_SYSTEM,
        )
        self._append_history(
            f"{self._format_elapsed()} | {end_note}",
            event_id=end_event_id,
            kind=self.HISTORY_KIND_SYSTEM,
        )

        if match_completed:
            self._persist_video_link_on_match_close()
            winner_name = (
                self.current_context.get("home_team", {}).get("name", "Casa")
                if match_winner == "home"
                else self.current_context.get("away_team", {}).get("name", "Ospiti")
            )
            final_note = (
                f"Fine incontro: vince {winner_name} "
                f"({home_sets_won}-{away_sets_won} set)"
            )
            final_event_id = self._persist_event(
                notes=final_note,
                kind=self.HISTORY_KIND_SYSTEM,
            )
            self._append_history(
                f"{self._format_elapsed()} | {final_note}",
                event_id=final_event_id,
                kind=self.HISTORY_KIND_SYSTEM,
            )
            self.subtitle.setText(final_note)
            QMessageBox.information(self, "Incontro concluso", final_note)
            next_set_number = None
        else:
            next_set_number = min(set_number + 1, 5)
            self.subtitle.setText(
                f"Set {set_number} chiuso. Torno alla formazione per il set {next_set_number}."
            )

        self.set_finished.emit(
            {
                "match_id": match_id,
                "completed_set_number": set_number,
                "next_set_number": next_set_number,
                "score_home": score_home,
                "score_away": score_away,
                "duration_seconds": int(max(0.0, float(self.elapsed_seconds_exact))),
                "home_sets_won": home_sets_won,
                "away_sets_won": away_sets_won,
                "match_completed": match_completed,
                "match_winner": match_winner,
            }
        )

    def _finish_match(self):
        """Chiude manualmente l'incontro e torna alla lista match."""
        if not self.current_context:
            return

        if self._is_editing_completed_match():
            QMessageBox.information(
                self,
                "Azione bloccata",
                "Fine Incontro è disabilitato in modalità modifica match terminato.",
            )
            return

        was_running = self.timer_running
        if self.timer_running:
            self._toggle_timer()

        match_id = self.current_context.get("match_id")
        set_number = int(self.current_context.get("set_number", 1) or 1)
        score_home = int(self.current_context.get("score_home", 0) or 0)
        score_away = int(self.current_context.get("score_away", 0) or 0)

        confirm = QMessageBox.question(
            self,
            "Conferma Fine Incontro",
            "Confermi la chiusura MANUALE dell'incontro?\n\n"
            f"Set corrente: {set_number}\n"
            f"Punteggio corrente: {score_home}-{score_away}\n"
            f"Durata set corrente: {self._format_elapsed()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            if was_running:
                self._toggle_timer()
            return

        confirm_final = QMessageBox.question(
            self,
            "Conferma finale",
            "Conferma DEFINITIVA chiusura incontro?\n"
            "Questa azione imposta lo stato partita su terminata.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm_final != QMessageBox.StandardButton.Yes:
            if was_running:
                self._toggle_timer()
            return

        home_sets_won = 0
        away_sets_won = 0
        match_winner = None

        self._persist_video_link_on_match_close()

        if self.db is not None and match_id is not None:
            try:
                with self.db.session_scope() as session:
                    from volleyball_scout.core.models import Match

                    set_record = self._ensure_set_record(session)
                    if set_record is not None:
                        set_record.score_home = score_home
                        set_record.score_away = score_away
                        set_record.duration = int(
                            max(0.0, float(self.elapsed_seconds_exact))
                        )
                        if set_record.winner is None and score_home != score_away:
                            set_record.winner = (
                                "home" if score_home > score_away else "away"
                            )

                    home_sets_won, away_sets_won = self._compute_sets_won(
                        session, match_id
                    )

                    if home_sets_won > away_sets_won:
                        match_winner = "home"
                    elif away_sets_won > home_sets_won:
                        match_winner = "away"
                    elif score_home != score_away:
                        match_winner = "home" if score_home > score_away else "away"

                    match_obj = session.query(Match).filter_by(id=match_id).first()
                    if match_obj is not None:
                        match_obj.status = "completed"
            except Exception as e:
                print(f"⚠️ Errore chiusura manuale incontro: {e}")

        winner_name = "N/D"
        if match_winner == "home":
            winner_name = self.current_context.get("home_team", {}).get("name", "Casa")
        elif match_winner == "away":
            winner_name = self.current_context.get("away_team", {}).get(
                "name", "Ospiti"
            )

        final_note = (
            "Fine incontro (manuale): "
            f"{self.current_context.get('home_team', {}).get('name', 'Casa')} "
            f"{home_sets_won} - {away_sets_won} "
            f"{self.current_context.get('away_team', {}).get('name', 'Ospiti')}"
        )

        final_event_id = self._persist_event(
            notes=final_note,
            kind=self.HISTORY_KIND_SYSTEM,
        )
        self._append_history(
            f"{self._format_elapsed()} | {final_note}",
            event_id=final_event_id,
            kind=self.HISTORY_KIND_SYSTEM,
        )

        self.subtitle.setText(final_note)
        QMessageBox.information(
            self,
            "Incontro concluso",
            f"Chiusura manuale completata.\nVincitore: {winner_name}",
        )

        self.set_finished.emit(
            {
                "match_id": match_id,
                "completed_set_number": set_number,
                "next_set_number": None,
                "score_home": score_home,
                "score_away": score_away,
                "duration_seconds": int(max(0.0, float(self.elapsed_seconds_exact))),
                "home_sets_won": home_sets_won,
                "away_sets_won": away_sets_won,
                "match_completed": True,
                "match_winner": match_winner,
                "manual_match_end": True,
            }
        )

    def _history_kind_from_event(self, event) -> str:
        raw_kind = str(getattr(event, "special_code", "") or "").upper()
        if raw_kind in {
            self.HISTORY_KIND_POINT,
            self.HISTORY_KIND_SKILL,
            self.HISTORY_KIND_SYSTEM,
        }:
            return raw_kind

        note = (getattr(event, "notes", "") or "").strip().lower()
        if note.startswith("punto"):
            return self.HISTORY_KIND_POINT
        if note.startswith("evento rapido"):
            return self.HISTORY_KIND_SKILL
        return self.HISTORY_KIND_SYSTEM

    def _load_set_state_from_db(self):
        """Carica punteggio/eventi già salvati del set corrente (se disponibili)."""
        self.current_set_id = None
        self.event_counter = 0
        self.history_records = []
        self.active_history_event_id = None
        self.events_list.clear()

        if self.db is None or not self.current_context:
            return

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import ScoutEvent

                set_record = self._ensure_set_record(session)
                if set_record is not None:
                    self.current_context["score_home"] = int(set_record.score_home or 0)
                    self.current_context["score_away"] = int(set_record.score_away or 0)
                    self.elapsed_seconds = int(set_record.duration or 0)
                    self.elapsed_seconds_exact = float(max(0, self.elapsed_seconds))

                    events = (
                        session.query(ScoutEvent)
                        .filter(
                            ScoutEvent.match_id == self.current_context.get("match_id")
                        )
                        .filter(ScoutEvent.set_id == set_record.id)
                        .order_by(ScoutEvent.id.asc())
                        .all()
                    )

                    for event in events:
                        note = event.notes or "Evento scouting"
                        timestamp_text = self._format_seconds(
                            int(getattr(event, "video_timestamp", 0) or 0)
                        )
                        event_timestamp = float(
                            max(
                                0.0,
                                float(getattr(event, "video_timestamp", 0.0) or 0.0),
                            )
                        )
                        self.history_records.append(
                            {
                                "text": f"{timestamp_text} | {note}",
                                "event_id": event.id,
                                "kind": self._history_kind_from_event(event),
                                "timestamp_seconds": event_timestamp,
                            }
                        )
                        if event.rally_number is not None:
                            self.event_counter = max(
                                self.event_counter, int(event.rally_number)
                            )

            self._apply_history_filter()

        except Exception as e:
            print(f"⚠️ Errore caricamento stato set: {e}")

    def load_match_context(self, context: dict):
        """Carica match e formazioni nella vista scouting live."""
        if not context:
            self.current_context = {}
            self.current_set_id = None
            self.event_counter = 0
            self.rally_history.clear()
            self.serving_side = "home"
            self.history_records = []
            self.active_history_event_id = None
            self.timeouts_used = {"home": 0, "away": 0}
            self.video_timestamp_seconds = None
            self.video_source_info = {}
            self.video_is_live = False
            self.video_paused = False
            self.timer_was_running_before_video_pause = False
            self._resume_video_seconds = None
            self._last_saved_video_second = None
            self.initial_service_selected = False
            self.setter_number_by_side = {"home": None, "away": None}
            self.reception_rotation_hint = {"home": "-", "away": "-"}
            self.reception_manual_positions = {"home": {}, "away": {}}
            self.point_outcome_map = self._load_point_outcome_map("global")
            self.events_list.clear()
            if self.timer_running:
                self._toggle_timer()
            self.elapsed_seconds = 0
            self.elapsed_seconds_exact = 0.0
            self._reset_timer_ui()

            self.subtitle.setText(
                "Conferma una formazione del primo set per iniziare lo scouting"
            )
            self.match_info.setText("Partita: -")
            self.set_info.setText("Set 1")
            self.home_score.setText("0")
            self.away_score.setText("0")
            self.home_court.update_lineup("Casa", {}, libero=None, serving=False)
            self.away_court.update_lineup("Trasferta", {}, libero=None, serving=False)
            self._clear_player_highlight()
            if hasattr(self, "code_input"):
                self.code_input.clear()
            self._set_code_team_side("home")
            self.set_video_resume_badge(None)
            self._update_video_pause_controls()
            self._refresh_video_mode_badge()
            self.set_match_mode_badge(editing_completed_match=False, match_status=None)
            self._update_initial_service_controls()
            self._update_outer_service_hints()
            self._set_controls_enabled(False)
            self.setFocus()
            return

        self.current_context = deepcopy(context)
        self.current_context.setdefault("score_home", 0)
        self.current_context.setdefault("score_away", 0)
        self.current_context.setdefault("set_number", 1)
        self.current_context.setdefault("home_team", {})
        self.current_context.setdefault("away_team", {})
        self.current_context["home_team"].setdefault("lineup", {})
        self.current_context["away_team"].setdefault("lineup", {})
        self.current_context["home_team"].setdefault("number_to_player_id", {})
        self.current_context["away_team"].setdefault("number_to_player_id", {})
        self.current_context.setdefault("reception_manual_positions", {})

        self.point_outcome_map = self._load_point_outcome_map()

        editing_completed_match = bool(
            self.current_context.get("editing_completed_match", False)
        )
        match_status = self.current_context.get("match_status")
        self.set_match_mode_badge(
            editing_completed_match=editing_completed_match,
            match_status=match_status,
        )

        self.rally_history.clear()
        self.active_history_event_id = None
        self.timeouts_used = {"home": 0, "away": 0}
        self.video_timestamp_seconds = None
        self.video_paused = False
        self._refresh_video_mode_badge()
        self._resume_video_seconds = self._load_video_resume_seconds(
            self.current_context.get("match_id")
        )
        self._last_saved_video_second = (
            int(self._resume_video_seconds)
            if self._resume_video_seconds is not None
            else None
        )
        self.set_video_resume_badge(self._resume_video_seconds)
        self.reception_rotation_hint = {"home": "-", "away": "-"}
        loaded_manual = self.current_context.get("reception_manual_positions", {})
        home_manual = dict(loaded_manual.get("home", {}))
        away_manual = dict(loaded_manual.get("away", {}))

        if not home_manual:
            home_manual = self._load_reception_positions_for_side("home")
        if not away_manual:
            away_manual = self._load_reception_positions_for_side("away")

        self.reception_manual_positions = {
            "home": home_manual,
            "away": away_manual,
        }
        self.current_context["reception_manual_positions"] = {
            "home": dict(self.reception_manual_positions.get("home", {})),
            "away": dict(self.reception_manual_positions.get("away", {})),
        }
        self.serving_side = self._resolve_serving_side(self.current_context)
        self._apply_serving_side(self.serving_side)
        if hasattr(self, "code_input"):
            self.code_input.clear()
        self._clear_player_highlight()

        self._load_set_state_from_db()
        if self._resume_video_seconds is not None:
            self.elapsed_seconds_exact = float(max(0.0, self._resume_video_seconds))
            self.elapsed_seconds = int(self.elapsed_seconds_exact)
        else:
            self.elapsed_seconds_exact = float(max(0, int(self.elapsed_seconds or 0)))
        self._refresh_setter_numbers()

        started_set = bool(self.history_records) or (
            int(self.current_context.get("score_home", 0) or 0)
            + int(self.current_context.get("score_away", 0) or 0)
            > 0
        )
        self.initial_service_selected = started_set

        home = self.current_context.get("home_team", {})
        away = self.current_context.get("away_team", {})
        match_id = self.current_context.get("match_id", "-")

        if self.initial_service_selected:
            self.subtitle.setText("Formazioni set caricate. Pronto per scoutizzare.")
        else:
            self.subtitle.setText(
                "Seleziona la battuta iniziale per iniziare lo scouting."
            )
        self.match_info.setText(
            f"Partita #{match_id}: {home.get('name', 'Casa')} vs {away.get('name', 'Trasferta')}"
        )
        self.set_info.setText(f"Set {self.current_context.get('set_number', 1)}")

        self._refresh_view()
        self._set_controls_enabled(True)
        self._update_video_pause_controls()

        if self.timer_running:
            self._toggle_timer()
        self._toggle_timer()
        self._highlight_history_by_current_time(scroll_to_active=False)
        self.setFocus()

    def closeEvent(self, event):
        if self.timer_running:
            self.timer.stop()
            self.timer_running = False
        super().closeEvent(event)

import json
import logging
import re
from copy import deepcopy

logger = logging.getLogger(__name__)

try:
    from volleyball_scout.core.rotation import rotate_lineup_clockwise
except ImportError:
    from ..core.rotation import rotate_lineup_clockwise

from PyQt6.QtCore import QPoint, QPointF, QRectF, QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen, QCursor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from .court_widgets import ServeTrajectoryOverlay
from .painted_court import PaintedCourt
from .formation_widget import FormationWidget
from .formation_editor import FormationCourtWidget
from .datavolley_codes import (
    parse_datavolley_code,
    resolve_point_team_from_evaluation,
    decode_point_outcome_map,
    point_outcome_map_to_text,
    parse_point_outcome_map_text,
    normalize_lineup_number,
    lineup_numbers_for_side,
    find_player_position_in_lineup,
)
from src.volley_analizer.core.dv_codes import describe_trajectory
from .formation_manager import FormationManager


class ReceptionCourtEditor(QWidget):
    """Editor visuale per posizionare manualmente i giocatori in ricezione."""

    MARKER_RADIUS = 18.0

    def __init__(self, team_side: str, parent=None):
        """Inizializza l'editor di ricezione con il lato squadra."""
        super().__init__(parent)
        self.team_side = "away" if team_side == "away" else "home"
        self.selected_player: str | None = None
        self._dragging_player: str | None = None
        self._positions: dict[str, tuple[float, float]] = {}
        self.setMinimumSize(520, 280)

    def set_selected_player(self, player_number: str | None):
        """Imposta il giocatore selezionato da evidenziare."""
        self.selected_player = str(player_number) if player_number else None
        self.update()

    def set_positions(self, positions: dict | None):
        """Imposta le posizioni dei giocatori sul campo."""
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
        """Restituisce le posizioni correnti dei giocatori."""
        return dict(self._positions)

    def clear_positions(self):
        """Pulisce tutte le posizioni dei giocatori."""
        self._positions = {}
        self.update()

    def _outer_rect(self) -> QRectF:
        # Calcola il rettangolo esterno con margine
        # Calcola il rettangolo esterno con margine
        margin = 12.0
        return QRectF(
            margin,
            margin,
            max(10.0, self.width() - margin * 2),
            max(10.0, self.height() - margin * 2),
        )

    def _team_half_rect(self) -> QRectF:
        # Restituisce la metà campo della squadra
        # Restituisce la metà campo della squadra
        outer = self._outer_rect()
        half_w = outer.width() / 2.0
        if self.team_side == "home":
            return QRectF(outer.left(), outer.top(), half_w, outer.height())
        return QRectF(outer.left() + half_w, outer.top(), half_w, outer.height())

    def _canvas_point(self, player_number: str) -> tuple[float, float] | None:
        # Converte coordinate normalizzate in pixel del canvas
        # Converte coordinate normalizzate in pixel del canvas
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
        # Trova il giocatore alle coordinate pixel date
        # Trova il giocatore alle coordinate pixel date
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
        # Imposta posizione normalizzata da coordinate canvas
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
        """Gestisce l'evento di pressione del mouse."""
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
        """Gestisce l'evento di movimento del mouse."""
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
        """Gestisce l'evento di rilascio del mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging_player = None
            self.update()
            return
        return super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Disegna il campo e i marcatori dei giocatori."""
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
        """Inizializza il dialogo di posizionamento ricezione."""
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
        # Aggiorna il giocatore selezionato nell'editor
        # Aggiorna il giocatore selezionato nell'editor
        current = self.player_selector.currentData()
        self.editor.set_selected_player(str(current) if current is not None else None)

    def _apply_rotation_preset(self):
        # Applica il preset di rotazione per il posizionamento
        # Applica il preset di rotazione per il posizionamento
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
        """Restituisce le posizioni inserite dall'utente."""
        return self.editor.positions()


class ScoutPanel(QWidget):
    """Schermata Scouting Live con doppio campo allineato."""

    set_finished = pyqtSignal(dict)
    back_requested = pyqtSignal()

    SKILL_CODES = {
        "Battuta": "S",
        "Ricezione": "R",
        "Alzata": "E",
        "Attacco": "A",
        "Muro": "B",
        "Difesa": "D",
    }

    CODE_SHORTCUTS = [
        ("Battuta", "SQ"),
        ("Ricezione", "RQ"),
        ("Alzata", "SE"),
        ("Attacco", "AH"),
        ("Muro", "BH"),
        ("Difesa", "DH"),
        ("Ace", "SQ#"),
        ("Err. Servizio", "SQ="),
        ("Punto", "#"),
        ("Errore", "="),
    ]

    KEYPAD_SKILL_TOKENS = ["SQ", "RQ", "SE", "AH", "BH", "DH", "FU"]
    KEYPAD_EVAL_TOKENS = ["#", "+", "!", "-", "=", "/"]
    KEYPAD_DIGIT_ROWS = [("7", "8", "9"), ("4", "5", "6"), ("1", "2", "3"), ("0",)]
    KEYPAD_MACRO_PRESETS = [
        ("Ace", "SQ#"),
        ("Err. Battuta", "SQ="),
        ("Pipe Punto", "AH#P"),
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
    DEFAULT_ATTACK_EVAL_SETTINGS_KEY = "default_attack_eval"
    VIDEO_SCREEN_INDEX_SETTINGS_KEY = "video_screen_index"
    VIDEO_MEMORY_SETTINGS_PREFIX = "video_resume_seconds_match_"
    RECEPTION_MEMORY_SETTINGS_PREFIX = "rx_manual_match_"
    RX_FORMATION_CONFIG_KEY = "rx_formation_config"
    RX_FORMATION_TEAM_PREFIX = "rx_formation_team_"
    HOTKEY_DEFAULTS = {
        "macro_1": "F1",
        "macro_2": "F2",
        "macro_3": "F3",
        "team_a": "F7",
        "team_b": "F8",
        "clear_code": "F9",
        "submit_code": "F10",
    }

    DATA_VOLLEY_SKILL_ALIASES = {
        "SQ": "S", "SH": "S", "SM": "S", "SF": "S", "S": "S", "V": "S",
        "RQ": "R", "R": "R",
        "SE": "E", "EH": "E", "EU": "E", "EQ": "E", "EO": "E", "EM": "E", "EP": "E", "E": "E",
        "AH": "A", "AU": "A", "AM": "A", "AQ": "A", "AO": "A", "TT": "A", "A": "A",
        "BH": "B", "BM": "B", "BO": "B", "BD": "B", "B": "B",
        "DH": "D", "D": "D",
        "FU": "F", "FH": "F", "F": "F",
    }

    DATA_VOLLEY_EVALUATIONS = {"#", "+", "!", "-", "=", "/"}

    HISTORY_KIND_POINT = "PT"
    HISTORY_KIND_SKILL = "SK"
    HISTORY_KIND_SYSTEM = "SY"

    def __init__(self, db_manager=None, parent=None):
        """Inizializza il pannello di scouting live."""
        super().__init__(parent)
        self.db = db_manager
        self.formation_manager = FormationManager(db_manager)
        self.current_context = {}
        self.serving_side = "home"
        self.rally_history = []
        self.current_set_id = None
        self.event_counter = 0
        self._history_target_index = None

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
        self.default_attack_eval = self._load_default_attack_eval()
        self.sync_timer_with_video = self._load_timer_sync_with_video()
        self.preferred_video_screen_index = self._load_video_screen_index()
        self.history_records = []
        self.timeouts_used = {"home": 0, "away": 0}

        # Sync video -> timestamp evento
        self.video_source_info = {}
        self.video_timestamp_seconds = None
        self.video_widget = None
        self.video_detached_window: QDialog | None = None
        self._is_docking_video = False
        self.video_is_live = False
        self.video_paused = False
        self.timer_was_running_before_video_pause = False
        self._resume_video_seconds: float | None = None
        self._last_saved_video_second: int | None = None

        self.history_timestamp_role = int(Qt.ItemDataRole.UserRole) + 1
        self.active_history_event_id: int | None = None

        self.initial_service_selected = False

        self._serve_mode_active = False
        self._reception_active = False
        self._serve_zone_start = None
        self._serve_zone_start_side = None
        self._serve_zone_end = None
        self._serve_zone_end_side = None
        self._serve_start_overlay_pos = None
        self._serve_receiver = None

        self._attack_mode_active = False
        self._attack_side = None
        self._attack_player = None
        self._attack_start_overlay_pos = None
        self._attack_start_zone = None
        self._attack_end_zone = None
        self._attack_end_side = None

        self.setter_number_by_side: dict[str, str | None] = {
            "home": None,
            "away": None,
        }
        self._libero_active_player: dict[str, str | None] = {
            "home": None,
            "away": None,
        }
        self._original_libero: dict[str, str | None] = {
            "home": None,
            "away": None,
        }
        self.reception_rotation_hint: dict[str, str] = {"home": "-", "away": "-"}
        self.reception_manual_positions: dict[str, dict[str, tuple[float, float]]] = {
            "home": {},
            "away": {},
        }
        self._formations_by_rotation: dict[str, dict[int, dict[str, tuple[float, float]]]] = {
            "home": {},
            "away": {},
        }

        self._setup_ui()
        self._set_controls_enabled(False)
        self._reset_timer_ui()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _setup_ui(self):
        # Costruisce l'interfaccia utente del pannello
        # Costruisce l'interfaccia utente del pannello
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        main_panel = QWidget()
        layout = QVBoxLayout(main_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("Scouting Live")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(
            "border: 1px solid #B79C8A; border-radius: 8px; padding: 4px;"
        )
        layout.addWidget(title)

        self.subtitle = QLabel(
            "Conferma una formazione del primo set per iniziare lo scouting"
        )
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.subtitle)

        self.match_info = QLabel("Partita: -")
        self.match_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_info.setStyleSheet("font-weight: bold; font-size: 11px;")
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

        self.set_scores_label = QLabel("")
        self.set_scores_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_scores_label.setStyleSheet("font-size: 11px; color: #999;")
        self.set_scores_label.setVisible(False)
        layout.addWidget(self.set_scores_label)

        scoreboard_layout = QHBoxLayout()
        scoreboard_layout.setSpacing(10)

        self.home_score = QLabel("0")
        self.home_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.home_score.setStyleSheet(
            "font-size: 18px; font-weight: bold; border: 1px solid #B79C8A; border-radius: 6px; padding: 4px 10px;"
        )

        self.btn_prev_set = QPushButton("<")
        self.btn_prev_set.setFixedWidth(32)
        self.btn_prev_set.setToolTip("Set precedente")
        self.btn_prev_set.clicked.connect(self._go_to_prev_set)

        self.set_info = QLabel("Set 1")
        self.set_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_info.setStyleSheet("font-weight: bold; font-size: 13px;")

        self.btn_next_set = QPushButton(">")
        self.btn_next_set.setFixedWidth(32)
        self.btn_next_set.setToolTip("Set successivo")
        self.btn_next_set.clicked.connect(self._go_to_next_set)

        self.away_score = QLabel("0")
        self.away_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.away_score.setStyleSheet(
            "font-size: 18px; font-weight: bold; border: 1px solid #B79C8A; border-radius: 6px; padding: 4px 10px;"
        )

        scoreboard_layout.addStretch()
        scoreboard_layout.addWidget(self.home_score)
        scoreboard_layout.addWidget(self.btn_prev_set)
        scoreboard_layout.addWidget(self.set_info)
        scoreboard_layout.addWidget(self.btn_next_set)
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

        score_buttons_layout.addWidget(self.btn_point_home)
        score_buttons_layout.addWidget(self.btn_point_away)
        score_buttons_layout.addWidget(self.btn_undo)
        score_buttons_layout.addWidget(self.btn_set_actions)
        score_buttons_layout.addWidget(self.btn_finish_set)
        score_buttons_layout.addWidget(self.btn_finish_match)
        score_buttons_layout.addWidget(self.btn_back_to_scouts)
        layout.addLayout(score_buttons_layout)

        hint = QLabel(
            "Imposta la battuta iniziale a inizio set. Poi servizio/rotazioni vengono gestiti automaticamente."
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-size: 9px; color: #D9CFC5;")
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

        self.home_court = PaintedCourt("home")
        self.home_court.cellClicked.connect(self._on_court_cell_clicked)
        self.home_court.liberoDropped.connect(self._on_libero_dropped)
        self.home_court.liberoRevertRequested.connect(self._on_libero_revert_requested)
        self.away_court = PaintedCourt("away")
        self.away_court.cellClicked.connect(self._on_court_cell_clicked)
        self.away_court.liberoDropped.connect(self._on_libero_dropped)
        self.away_court.liberoRevertRequested.connect(self._on_libero_revert_requested)

        # Nomi squadre e stato sopra i campi
        team_names_row = QHBoxLayout()
        team_names_row.setContentsMargins(0, 0, 0, 0)
        team_names_row.setSpacing(0)

        self.home_team_label = QPushButton("CASA")
        self.home_team_label.setFlat(True)
        self.home_team_label.setEnabled(False)
        self.home_team_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #F6EFE9;"
            "border: 1px solid #6B7280; border-radius: 8px; padding: 6px 4px;"
            "background-color: #374151;"
        )

        self.away_team_label = QPushButton("OSPITI")
        self.away_team_label.setFlat(True)
        self.away_team_label.setEnabled(False)
        self.away_team_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #F6EFE9;"
            "border: 1px solid #6B7280; border-radius: 8px; padding: 6px 4px;"
            "background-color: #374151;"
        )

        team_names_row.addWidget(self.home_team_label, 1)
        # Spazio per la rete al centro
        net_spacer = QFrame()
        net_spacer.setFixedWidth(3)
        net_spacer.setStyleSheet("background: transparent;")
        team_names_row.addWidget(net_spacer)
        team_names_row.addWidget(self.away_team_label, 1)
        layout.addLayout(team_names_row)

        courts_container = QWidget()
        self.courts_container = courts_container
        courts_container.setStyleSheet(
            "QWidget { background-color: transparent; }"
        )
        courts_container.setLayout(QHBoxLayout())
        courts_container.layout().setContentsMargins(0, 0, 0, 0)
        courts_container.layout().setSpacing(0)

        # Contenitore fisso per pulsante BATTUTA (largo 60px, sempre visibile)
        home_battuta_container = QWidget()
        home_battuta_container.setFixedWidth(60)
        home_battuta_container.setStyleSheet("background: transparent;")
        home_battuta_layout = QVBoxLayout(home_battuta_container)
        home_battuta_layout.setContentsMargins(0, 0, 0, 0)

        self.home_battuta_btn = QPushButton("BATTUTA")
        self.home_battuta_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.home_battuta_btn.setVisible(False)
        self.home_battuta_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.home_battuta_btn.clicked.connect(
            lambda: self._on_battuta_badge_clicked("home")
        )
        home_battuta_layout.addWidget(self.home_battuta_btn)
        courts_container.layout().addWidget(home_battuta_container)

        courts_container.layout().addWidget(self.home_court, 1)
        # Riga di rete (linea bianca sottile)
        net_line = QFrame()
        net_line.setFixedWidth(2)
        net_line.setStyleSheet("background-color: #FFFFFF;")
        courts_container.layout().addWidget(net_line)
        # Piccola ombreggiatura per effetto rete
        net_shadow = QFrame()
        net_shadow.setFixedWidth(1)
        net_shadow.setStyleSheet("background-color: rgba(255,255,255,80);")
        courts_container.layout().addWidget(net_shadow)
        courts_container.layout().addWidget(self.away_court, 1)

        away_battuta_container = QWidget()
        away_battuta_container.setFixedWidth(60)
        away_battuta_container.setStyleSheet("background: transparent;")
        away_battuta_layout = QVBoxLayout(away_battuta_container)
        away_battuta_layout.setContentsMargins(0, 0, 0, 0)

        self.away_battuta_btn = QPushButton("BATTUTA")
        self.away_battuta_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.away_battuta_btn.setVisible(False)
        self.away_battuta_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.away_battuta_btn.clicked.connect(
            lambda: self._on_battuta_badge_clicked("away")
        )
        away_battuta_layout.addWidget(self.away_battuta_btn)
        courts_container.layout().addWidget(away_battuta_container)

        self.serve_overlay = ServeTrajectoryOverlay(courts_container)
        self.serve_overlay.setGeometry(courts_container.rect())
        courts_container.installEventFilter(self)

        self._court_stack = QStackedWidget()
        self._court_stack.addWidget(courts_container)
        self._formation_view = FormationWidget()
        self._court_stack.addWidget(self._formation_view)
        self._court_stack.setCurrentIndex(0)
        layout.addWidget(self._court_stack, 1)

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
        self.btn_formazioni = QPushButton("Formazioni ricezione")
        self.btn_formazioni.setToolTip(
            "Apri l'editor formazioni per rotazione (drag-and-drop)"
        )
        self.btn_formazioni.clicked.connect(self._open_formation_editor)
        reception_row.addWidget(self.btn_formazioni)

        self.btn_toggle_court_view = QPushButton("Vista formazione")
        self.btn_toggle_court_view.setCheckable(True)
        self.btn_toggle_court_view.setToolTip(
            "Alterna tra vista campo e vista formazione compatta"
        )
        self.btn_toggle_court_view.toggled.connect(self._toggle_court_view)
        reception_row.addWidget(self.btn_toggle_court_view)

        self._reception_eval_buttons = []
        self._eval_label = QLabel("  R:")
        self._eval_label.setVisible(False)
        self._eval_label.setStyleSheet("font-weight: bold; color: #E5E7EB;")
        reception_row.addWidget(self._eval_label)
        for eval_code in ["#", "+", "!", "/", "-", "="]:
            btn = QPushButton(eval_code)
            btn.setFixedSize(34, 34)
            btn.setVisible(False)
            btn.setStyleSheet(
                "font-weight: bold; font-size: 14px; background-color: #4B5563;"
                "color: #F6EFE9; border: 1px solid #6B7280; border-radius: 17px;"
            )
            btn.clicked.connect(lambda checked, e=eval_code: self._on_reception_eval_clicked(e))
            reception_row.addWidget(btn)
            self._reception_eval_buttons.append(btn)

        self._attack_eval_buttons = []
        self._attack_eval_label = QLabel("  Attacco:")
        self._attack_eval_label.setVisible(False)
        self._attack_eval_label.setStyleSheet("font-weight: bold; color: #E5E7EB;")
        reception_row.addWidget(self._attack_eval_label)
        for eval_code in ["#", "+", "!", "/", "-", "="]:
            btn = QPushButton(eval_code)
            btn.setFixedSize(34, 34)
            btn.setVisible(False)
            btn.setStyleSheet(
                "font-weight: bold; font-size: 14px; background-color: #D97706;"
                "color: #FFF; border: 1px solid #F59E0B; border-radius: 17px;"
            )
            btn.clicked.connect(lambda checked, e=eval_code: self._on_attack_eval_clicked(e))
            reception_row.addWidget(btn)
            self._attack_eval_buttons.append(btn)

        reception_row.addStretch()
        layout.addLayout(reception_row)

        self.trajectory_desc_label = QLabel("")
        self.trajectory_desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trajectory_desc_label.setVisible(False)
        self.trajectory_desc_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #FCD34D;"
            "background-color: #1E3A5F; border: 1px solid #3B82F6;"
            "border-radius: 6px; padding: 4px 12px;"
        )
        traj_row = QHBoxLayout()
        traj_row.addStretch()
        traj_row.addWidget(self.trajectory_desc_label)
        traj_row.addStretch()
        layout.addLayout(traj_row)

        datavolley_group = QGroupBox("Codifica DataVolley")
        datavolley_layout = QVBoxLayout(datavolley_group)
        datavolley_layout.setSpacing(2)
        datavolley_layout.setContentsMargins(4, 4, 4, 4)

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

        self._create_datavolley_keypad(datavolley_layout)

        layout.addWidget(datavolley_group)

        root_layout.addWidget(main_panel, 3)

        history_panel = QWidget()
        history_side_layout = QVBoxLayout(history_panel)
        history_side_layout.setContentsMargins(0, 0, 0, 0)
        history_side_layout.setSpacing(4)

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
        self.video_group_layout.addWidget(self.video_placeholder)

        video_actions_row = QHBoxLayout()
        self.btn_video_detach = QPushButton("Finestra esterna")
        self.btn_video_detach.clicked.connect(self._detach_video_to_window)
        video_actions_row.addWidget(self.btn_video_detach)

        self.video_screen_selector = QComboBox()
        self.video_screen_selector.setToolTip("Seleziona il monitor destinazione")
        self.video_screen_selector.currentIndexChanged.connect(
            self._on_video_screen_selector_changed
        )
        video_actions_row.addWidget(self.video_screen_selector)

        self.btn_video_move_monitor = QPushButton("Sposta monitor")
        self.btn_video_move_monitor.clicked.connect(self._move_video_to_selected_screen)
        video_actions_row.addWidget(self.btn_video_move_monitor)

        self.btn_video_dock = QPushButton("Schermo diviso")
        self.btn_video_dock.clicked.connect(self._dock_video_in_panel)
        video_actions_row.addWidget(self.btn_video_dock)

        self.video_group_layout.addLayout(video_actions_row)
        history_side_layout.addWidget(self.video_group)

        self.codes_group = QGroupBox("Cronologia")
        history_layout = QVBoxLayout(self.codes_group)

        history_filter_row = QHBoxLayout()
        history_filter_row.addWidget(QLabel("Filtro:"))
        self.history_filter = QComboBox()
        self.history_filter.addItems(["Tutti", "Punti", "Skill", "Sistema"])
        self.history_filter.currentTextChanged.connect(self._apply_history_filter)
        history_filter_row.addWidget(self.history_filter)
        history_filter_row.addStretch()
        history_layout.addLayout(history_filter_row)

        self.events_list = QTableWidget()
        self.events_list.setColumnCount(7)
        self.events_list.setHorizontalHeaderLabels([
            "CODICE", "FLAGS", "AZIONE", "PUNTI", "SET", "TEMPO", "ORARIO"
        ])
        self.events_list.horizontalHeader().setStretchLastSection(False)
        self.events_list.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.events_list.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.events_list.verticalHeader().setVisible(False)
        self.events_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.events_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.events_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.events_list.setAlternatingRowColors(True)
        self.events_list.verticalHeader().setDefaultSectionSize(20)
        self.events_list.setShowGrid(False)
        self.events_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.events_list.customContextMenuRequested.connect(
            self._open_events_context_menu
        )
        self.events_list.cellDoubleClicked.connect(self._on_event_cell_double_clicked)
        font = QFont("Monospace", 8)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.events_list.setFont(font)
        self.events_list.setStyleSheet("""
            QTableWidget {
                background-color: #2B211C;
                alternate-background-color: #332620;
                border: 1px solid #6E4B32;
                gridline-color: #4A3528;
                color: #F6EFE9;
            }
            QTableWidget::item {
                padding: 2px 6px;
                border: none;
                color: #F6EFE9;
            }
            QTableWidget::item:selected {
                background-color: #6E4B32;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #1A1410;
                color: #EBD8C5;
                font-weight: bold;
                font-size: 9px;
                padding: 3px 6px;
                border: none;
                border-right: 1px solid #4A3528;
                font-family: monospace;
            }
        """)
        history_layout.addWidget(self.events_list)

        history_side_layout.addWidget(self.codes_group, 1)
        root_layout.addWidget(history_panel, 2)

        self._refresh_screen_selector()

    def _toggle_court_view(self, use_formation: bool):
        if use_formation:
            self._court_stack.setCurrentIndex(1)
            self.btn_toggle_court_view.setText("Vista campo")
        else:
            self._court_stack.setCurrentIndex(0)
            self.btn_toggle_court_view.setText("Vista formazione")
        self._sync_formation_view()

    def _sync_formation_view(self):
        if not hasattr(self, "_formation_view"):
            return
        home = self.current_context.get("home_team", {}) if self.current_context else {}
        away = self.current_context.get("away_team", {}) if self.current_context else {}
        self._formation_view.update_lineups(
            home.get("lineup", {}),
            away.get("lineup", {}),
            rotation=self._get_current_rotation_for_sync(),
        )
        self._formation_view.set_libero(
            home.get("libero"),
            away.get("libero"),
        )
        self._formation_view.set_setter(
            self.setter_number_by_side.get("home"),
            self.setter_number_by_side.get("away"),
        )

    def _get_current_rotation_for_sync(self):
        rot = self._get_current_rotation("home")
        if rot is None:
            rot = self._get_current_rotation("away")
        if rot is None:
            return 1
        return max(1, min(6, rot))

    def _toggle_codes_panel(self, is_visible: bool):
        # Mostra o nasconde il pannello dei codici
        # Mostra o nasconde il pannello dei codici
        self.codes_group.setVisible(is_visible)
        self.btn_toggle_codes.setText(
            "Nascondi elenco codici" if is_visible else "Mostra elenco codici"
        )

    def _toggle_keypad_panel(self, visible: bool):
        # Mostra o nasconde il tastierino DataVolley
        # Mostra o nasconde il tastierino DataVolley
        if hasattr(self, "datavolley_keypad_group"):
            self.datavolley_keypad_group.setVisible(bool(visible))
        if hasattr(self, "btn_toggle_keypad"):
            self.btn_toggle_keypad.setText(
                "Nascondi tastierino" if visible else "Mostra tastierino"
            )

    def _refresh_screen_selector(self):
        # Aggiorna la lista dei monitor disponibili
        # Aggiorna la lista dei monitor disponibili
        if not hasattr(self, "video_screen_selector"):
            return

        previous_data = self.video_screen_selector.currentData()
        self.video_screen_selector.blockSignals(True)
        self.video_screen_selector.clear()

        screens = QGuiApplication.screens()
        for idx, screen in enumerate(screens):
            try:
                name = str(screen.name() or f"Monitor {idx + 1}")
            except Exception:
                name = f"Monitor {idx + 1}"
            self.video_screen_selector.addItem(f"{idx + 1}: {name}", idx)

        if self.video_screen_selector.count() <= 0:
            self.video_screen_selector.blockSignals(False)
            return

        selected_data = previous_data
        if selected_data is None:
            selected_data = int(max(0, self.preferred_video_screen_index))

        selected_index = self.video_screen_selector.findData(selected_data)
        if selected_index < 0:
            selected_index = min(
                self.video_screen_selector.count() - 1,
                int(max(0, self.preferred_video_screen_index)),
            )
        if selected_index < 0:
            selected_index = 0

        self.video_screen_selector.setCurrentIndex(selected_index)
        selected_data_now = self.video_screen_selector.itemData(selected_index)
        try:
            self.preferred_video_screen_index = max(0, int(selected_data_now))
        except Exception:
            self.preferred_video_screen_index = 0

        self.video_screen_selector.blockSignals(False)
        self._save_video_screen_index()

    def eventFilter(self, obj, event):
        if obj is self.courts_container and event.type() == event.Type.Resize:
            self.serve_overlay.setGeometry(self.courts_container.rect())
        return super().eventFilter(obj, event)

    def _on_video_screen_selector_changed(self, _index: int):
        # Salva il monitor selezionato quando cambia
        # Salva il monitor selezionato quando cambia
        if not hasattr(self, "video_screen_selector"):
            return

        raw = self.video_screen_selector.currentData()
        try:
            self.preferred_video_screen_index = max(0, int(raw))
        except Exception:
            self.preferred_video_screen_index = 0
        self._save_video_screen_index()

    def _selected_screen_index(self) -> int:
        # Restituisce l'indice del monitor selezionato
        # Restituisce l'indice del monitor selezionato
        if not hasattr(self, "video_screen_selector"):
            return 0

        raw = self.video_screen_selector.currentData()
        try:
            return max(0, int(raw))
        except Exception:
            return 0

    def _remove_video_widget_from_current_parent(self):
        # Rimuove il video widget dal suo genitore corrente
        # Rimuove il video widget dal suo genitore corrente
        if self.video_widget is None:
            return

        parent = self.video_widget.parentWidget()
        if parent is not None and parent.layout() is not None:
            parent.layout().removeWidget(self.video_widget)
        self.video_widget.setParent(None)

    def _attach_video_widget_to_panel(self):
        # Collega il video widget al pannello principale
        # Collega il video widget al pannello principale
        if self.video_widget is None:
            return

        self._remove_video_widget_from_current_parent()
        self.video_widget.setParent(self.video_group)
        self.video_group_layout.insertWidget(2, self.video_widget, 1)
        if hasattr(self, "video_placeholder"):
            self.video_placeholder.setVisible(False)

    def _on_video_detached_window_closed(self, *_args):
        # Riporta il video nel pannello quando la finestra esterna viene chiusa
        # Riporta il video nel pannello quando la finestra esterna viene chiusa
        if self._is_docking_video:
            return
        if self.video_widget is None:
            self.video_detached_window = None
            self._update_video_layout_controls()
            return
        self._dock_video_in_panel()

    def _update_video_layout_controls(self):
        # Aggiorna lo stato dei controlli di layout video
        # Aggiorna lo stato dei controlli di layout video
        has_video = self.video_widget is not None
        detached = self.video_detached_window is not None

        self._refresh_screen_selector()
        screens_count = len(QGuiApplication.screens())
        can_move_monitor = has_video and screens_count > 0

        if hasattr(self, "btn_video_detach"):
            self.btn_video_detach.setEnabled(has_video and not detached)
        if hasattr(self, "video_screen_selector"):
            self.video_screen_selector.setEnabled(can_move_monitor)
        if hasattr(self, "btn_video_move_monitor"):
            self.btn_video_move_monitor.setEnabled(can_move_monitor)
        if hasattr(self, "btn_video_dock"):
            self.btn_video_dock.setEnabled(has_video and detached)

    def _detach_video_to_window(self):
        # Sposta il video in una finestra esterna
        # Sposta il video in una finestra esterna
        if self.video_widget is None:
            return

        if self.video_detached_window is not None:
            self.video_detached_window.show()
            self.video_detached_window.raise_()
            self.video_detached_window.activateWindow()
            return

        self._remove_video_widget_from_current_parent()

        window = QDialog(self)
        window.setWindowTitle("Video Scout - finestra esterna")
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        window.setModal(False)

        layout = QVBoxLayout(window)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.video_widget.setParent(window)
        layout.addWidget(self.video_widget, 1)

        window.resize(960, 540)
        window.finished.connect(self._on_video_detached_window_closed)
        self.video_detached_window = window

        window.show()
        window.raise_()
        window.activateWindow()

        self._update_video_layout_controls()
        self._update_video_pause_controls()

    def _move_video_to_selected_screen(self):
        # Sposta il video sul monitor selezionato
        # Sposta il video sul monitor selezionato
        if self.video_widget is None:
            return

        screens = QGuiApplication.screens()
        if len(screens) <= 0:
            QMessageBox.information(
                self,
                "Monitor non trovato",
                "Nessun monitor rilevato dal sistema.",
            )
            return

        selected_idx = self._selected_screen_index()
        if selected_idx >= len(screens):
            selected_idx = 0

        self._detach_video_to_window()
        if self.video_detached_window is None:
            return

        target = screens[selected_idx]
        geo = target.availableGeometry()
        margin = 20
        width = max(640, int(geo.width() - margin * 2))
        height = max(360, int(geo.height() - margin * 2))

        self.video_detached_window.setGeometry(
            int(geo.x() + margin),
            int(geo.y() + margin),
            int(width),
            int(height),
        )
        self.video_detached_window.show()
        self.video_detached_window.raise_()
        self.video_detached_window.activateWindow()

        self._update_video_layout_controls()

    def _move_video_to_secondary_screen(self):
        """Compatibilità retro: usa monitor 2 se presente, altrimenti monitor principale."""
        if hasattr(self, "video_screen_selector"):
            preferred = 1 if self.video_screen_selector.count() > 1 else 0
            self.video_screen_selector.setCurrentIndex(preferred)
        self._move_video_to_selected_screen()

    def _dock_video_in_panel(self):
        # Riporta il video dalla finestra esterna al pannello
        # Riporta il video dalla finestra esterna al pannello
        if self.video_widget is None:
            self.video_detached_window = None
            self._update_video_layout_controls()
            self._update_video_pause_controls()
            return

        self._is_docking_video = True
        try:
            window = self.video_detached_window
            self.video_detached_window = None
            if window is not None:
                try:
                    window.finished.disconnect(self._on_video_detached_window_closed)
                except Exception:
                    pass
                window.hide()
                window.deleteLater()

            self._attach_video_widget_to_panel()
        finally:
            self._is_docking_video = False

        self._update_video_layout_controls()
        self._update_video_pause_controls()

    def set_video_widget(self, widget: QWidget | None):
        """Imposta o rimuove il widget video nel pannello."""
        if not hasattr(self, "video_group_layout"):
            return

        if self.video_widget is not None:
            self._remove_video_widget_from_current_parent()
            self.video_widget = None

        if widget is None:
            if self.video_detached_window is not None:
                self._is_docking_video = True
                try:
                    self.video_detached_window.hide()
                    self.video_detached_window.deleteLater()
                finally:
                    self._is_docking_video = False
                self.video_detached_window = None
            if hasattr(self, "video_placeholder"):
                self.video_placeholder.setVisible(True)
            self._update_video_layout_controls()
            self._update_video_pause_controls()
            return

        self.video_widget = widget
        self._attach_video_widget_to_panel()
        self._update_video_layout_controls()
        self._update_video_pause_controls()

    def _request_back_to_scouts(self):
        # Richiede il ritorno alla lista scout
        # Richiede il ritorno alla lista scout
        self.back_requested.emit()

    def _set_video_mode_badge(self, text: str, color: str, border: str):
        # Imposta il badge con testo e colori per la modalità video
        # Imposta il badge con testo e colori per la modalità video
        if not hasattr(self, "video_mode_badge"):
            return
        self.video_mode_badge.setText(text)
        self.video_mode_badge.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #F8FAFC;"
            f"background-color: {color}; border: 1px solid {border};"
            "border-radius: 8px; padding: 3px 8px;"
        )

    def _refresh_video_mode_badge(self):
        # Aggiorna il badge della modalità video
        # Aggiorna il badge della modalità video
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
        # Aggiorna lo stato del pulsante pausa video
        # Aggiorna lo stato del pulsante pausa video
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
        # Mette in pausa o riprende video e timer insieme
        # Mette in pausa o riprende video e timer insieme
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
        """Aggiorna lo stato di riproduzione del video."""
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
        # Restituisce le impostazioni QSettings per le scorciatoie
        return QSettings(self.SHORTCUTS_SETTINGS_ORG, self.SHORTCUTS_SETTINGS_APP)

    def _video_memory_key(self, match_id) -> str | None:
        # Genera la chiave per salvare il tempo video di ripresa
        try:
            parsed = int(match_id)
            if parsed <= 0:
                return None
            return f"{self.VIDEO_MEMORY_SETTINGS_PREFIX}{parsed}"
        except Exception:
            return None

    def _load_video_resume_seconds(self, match_id) -> float | None:
        # Carica i secondi di ripresa video salvati
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
        # Salva i secondi di ripresa video correnti
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
        """Restituisce i secondi di ripresa video salvati."""
        return self._resume_video_seconds

    def set_video_resume_badge(self, seconds: float | None):
        """Mostra o nasconde il badge di ripresa video."""
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
        """Imposta il badge della modalità partita."""
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
        # Carica la modalità dimensione tastierino
        settings = self._shortcuts_settings()
        value = settings.value(self.KEYPAD_SIZE_SETTINGS_KEY, "compact", type=str)
        mode = str(value or "compact").strip().lower()
        return mode if mode in {"compact", "large"} else "compact"

    def _save_keypad_size_mode(self):
        # Salva la modalità dimensione tastierino
        settings = self._shortcuts_settings()
        settings.setValue(self.KEYPAD_SIZE_SETTINGS_KEY, self.keypad_size_mode)

    def _keypad_button_height(self) -> int:
        # Restituisce l'altezza dei pulsanti tastierino
        return 38 if self.keypad_size_mode == "large" else 30

    def _scale_keypad_width(self, base_width: int | None) -> int | None:
        # Scala la larghezza in base alla modalità
        if base_width is None:
            return None
        if self.keypad_size_mode == "large":
            return int(base_width * 1.2)
        return base_width

    def _apply_keypad_size_mode(self):
        # Applica la dimensione dei pulsanti tastierino
        min_h = self._keypad_button_height()
        for btn in self.code_keypad_buttons:
            btn.setMinimumHeight(min_h)
            base_width = btn.property("base_max_width")
            if isinstance(base_width, int) and base_width > 0:
                btn.setMaximumWidth(self._scale_keypad_width(base_width) or base_width)

    def _on_keypad_size_changed(self):
        # Gestisce il cambio dimensione tastierino
        if not hasattr(self, "keypad_size_selector"):
            return

        selected = self.keypad_size_selector.currentData()
        mode = "large" if selected == "large" else "compact"
        self.keypad_size_mode = mode
        self._save_keypad_size_mode()
        self._apply_keypad_size_mode()

    def _load_keyboard_mode_enabled(self) -> bool:
        # Carica se la modalità solo tastiera è attiva
        settings = self._shortcuts_settings()
        value = settings.value(self.KEYBOARD_MODE_SETTINGS_KEY, "0", type=str)
        return str(value or "0").strip() in {"1", "true", "True", "yes"}

    def _save_keyboard_mode_enabled(self):
        # Salva lo stato della modalità solo tastiera
        settings = self._shortcuts_settings()
        settings.setValue(
            self.KEYBOARD_MODE_SETTINGS_KEY, "1" if self.keyboard_only_mode else "0"
        )

    def _load_timer_sync_with_video(self) -> bool:
        # Carica l'impostazione di sincronizzazione timer con video
        settings = self._shortcuts_settings()
        value = settings.value(self.TIMER_SYNC_WITH_VIDEO_SETTINGS_KEY, "1", type=str)
        return str(value or "1").strip().lower() in {"1", "true", "yes"}

    def _save_timer_sync_with_video(self):
        # Salva l'impostazione di sincronizzazione timer con video
        settings = self._shortcuts_settings()
        settings.setValue(
            self.TIMER_SYNC_WITH_VIDEO_SETTINGS_KEY,
            "1" if self.sync_timer_with_video else "0",
        )

    def _load_default_attack_eval(self) -> str:
        # Carica la valutazione attacco predefinita
        settings = self._shortcuts_settings()
        value = settings.value(self.DEFAULT_ATTACK_EVAL_SETTINGS_KEY, "!", type=str)
        eval_code = str(value or "!").strip()
        return eval_code if eval_code in {"#", "+", "!", "/", "-", "="} else "!"

    def _save_default_attack_eval(self):
        # Salva la valutazione attacco predefinita
        settings = self._shortcuts_settings()
        settings.setValue(self.DEFAULT_ATTACK_EVAL_SETTINGS_KEY, self.default_attack_eval)

    def _load_rx_formation_config(self, scope: str | None = None) -> dict:
        # Carica la configurazione formazioni ricezione
        settings = self._shortcuts_settings()
        if scope == "global" or scope is None:
            key = self.RX_FORMATION_CONFIG_KEY
        else:
            key = f"{self.RX_FORMATION_TEAM_PREFIX}{scope}"
        raw = settings.value(key, "", type=str)
        if not raw:
            return {}
        try:
            import json
            data = json.loads(str(raw))
            if not isinstance(data, dict):
                return {}
            normalized = {}
            for k, v in data.items():
                try:
                    normalized[int(k)] = v
                except (ValueError, TypeError):
                    normalized[k] = v
            if self.formation_manager.is_old_format_config(normalized):
                normalized = self.formation_manager.convert_to_new_format(normalized)
            return normalized
        except Exception:
            return {}

    def _save_rx_formation_config(self, data: dict, scope: str | None = None):
        # Salva la configurazione formazioni ricezione
        settings = self._shortcuts_settings()
        if scope == "global" or scope is None:
            key = self.RX_FORMATION_CONFIG_KEY
        else:
            key = f"{self.RX_FORMATION_TEAM_PREFIX}{scope}"
        import json
        settings.setValue(key, json.dumps(data, ensure_ascii=False))

    def _rx_formation_for_side(self, side: str) -> dict:
        # Restituisce la configurazione ricezione per una squadra
        config = self._load_rx_formation_config("global")
        if config:
            return config
        team_id = self._team_context(side).get("id")
        if team_id:
            team_config = self._load_rx_formation_config(str(team_id))
            if team_config:
                return team_config
        return {}

    def _load_video_screen_index(self) -> int:
        # Carica l'indice del monitor preferito per il video
        settings = self._shortcuts_settings()
        value = settings.value(self.VIDEO_SCREEN_INDEX_SETTINGS_KEY, "0", type=str)
        try:
            return max(0, int(str(value or "0").strip()))
        except Exception:
            return 0

    def _save_video_screen_index(self):
        # Salva l'indice del monitor preferito per il video
        settings = self._shortcuts_settings()
        settings.setValue(
            self.VIDEO_SCREEN_INDEX_SETTINGS_KEY,
            str(max(0, int(self.preferred_video_screen_index))),
        )

    def _hotkey_action_definitions(self) -> list[tuple[str, str, bool]]:
        # Restituisce la lista delle definizioni azioni hotkey
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
        # Normalizza un token hotkey F1-F12
        value = str(token or "").strip().upper()
        if re.fullmatch(r"F([1-9]|1[0-2])", value):
            return value
        return None

    def _qt_key_to_hotkey_token(self, key: int) -> str | None:
        # Converte un tasto Qt in token hotkey
        for idx in range(1, 13):
            qt_key = getattr(Qt.Key, f"Key_F{idx}", None)
            if qt_key is not None and key == int(qt_key):
                return f"F{idx}"
        return None

    def _default_hotkey_map(self) -> dict[str, str]:
        # Restituisce la mappa hotkey predefinita
        defaults = {}
        valid_actions = {action for action, _, _ in self._hotkey_action_definitions()}
        for action, token in self.HOTKEY_DEFAULTS.items():
            if action in valid_actions:
                normalized = self._normalize_hotkey_token(token)
                if normalized:
                    defaults[action] = normalized
        return defaults

    def _load_hotkey_map(self) -> dict[str, str]:
        # Carica la mappa hotkey salvata
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
        # Salva la mappa hotkey corrente
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
        # Trova conflitti nella mappa hotkey
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
        # Formatta i conflitti hotkey in testo leggibile
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
        # Restituisce le associazioni hotkey attive
        bindings = {}
        defaults = self._default_hotkey_map()
        for action, _, _ in self._hotkey_action_definitions():
            token = self.hotkey_map.get(action) or defaults.get(action)
            token_norm = self._normalize_hotkey_token(token)
            if token_norm and token_norm not in bindings:
                bindings[token_norm] = action
        return bindings

    def _hotkeys_to_text(self, hotkey_map: dict[str, str]) -> str:
        # Converte la mappa hotkey in testo modificabile
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
        # Analizza il testo della mappa hotkey
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
        # Mostra il dialogo di configurazione hotkey
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
        # Reimposta la mappa hotkey ai valori predefiniti
        self.hotkey_map = self._default_hotkey_map()
        self._save_hotkey_map()
        self._update_keyboard_hotkeys_hint()
        self._update_hotkeys_map_label()

    def _point_outcome_scope_options(self) -> list[tuple[str, str]]:
        # Restituisce le opzioni di scope per la mappa punti
        return [
            ("global", "Globale"),
            ("match", "Solo match corrente"),
            ("set", "Solo set corrente"),
        ]

    def _load_point_outcome_scope(self) -> str:
        # Carica lo scope della mappa punto
        settings = self._shortcuts_settings()
        value = settings.value(
            self.POINT_OUTCOME_SCOPE_SETTINGS_KEY, "global", type=str
        )
        scope = str(value or "global").strip().lower()
        valid = {key for key, _ in self._point_outcome_scope_options()}
        return scope if scope in valid else "global"

    def _save_point_outcome_scope(self):
        # Salva lo scope della mappa punto
        settings = self._shortcuts_settings()
        settings.setValue(
            self.POINT_OUTCOME_SCOPE_SETTINGS_KEY, self.point_outcome_scope
        )

    def _point_outcome_storage_key(self, scope: str | None = None) -> str:
        # Genera la chiave di archiviazione per la mappa punti
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

    def _load_point_outcome_map(self, scope: str | None = None) -> dict[str, str]:
        # Carica la mappa punto vinto/perso
        settings = self._shortcuts_settings()
        key = self._point_outcome_storage_key(scope)
        serialized = settings.value(key, "", type=str)
        return decode_point_outcome_map(serialized)

    def _save_point_outcome_map(self, scope: str | None = None):
        # Salva la mappa punto vinto/perso
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

    def _configure_point_outcome_map(self):
        # Mostra il dialogo di configurazione mappa punti
        current_text = point_outcome_map_to_text(self.point_outcome_map)
        new_text, ok = QInputDialog.getMultiLineText(
            self,
            "Mappa punto vinto/perso",
            "Configura le regole punto (Skill+Valutazione -> esito)",
            current_text,
        )
        if not ok:
            return

        parsed = parse_point_outcome_map_text(new_text)
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
        # Restituisce il testo di anteprima delle scorciatoie
        if not self.code_shortcuts:
            return "Tasti rapidi codifica: -"
        preview = [f"{label}→{token}" for label, token in self.code_shortcuts[:6]]
        suffix = " ..." if len(self.code_shortcuts) > 6 else ""
        return "Tasti rapidi codifica: " + " | ".join(preview) + suffix

    def _hotkeys_preview_text(self) -> str:
        # Restituisce il testo di anteprima delle hotkey
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
        # Restituisce il testo di anteprima della mappa punti
        scope_label = dict(self._point_outcome_scope_options()).get(
            self.point_outcome_scope, self.point_outcome_scope
        )
        keys = sorted(self.point_outcome_map.keys())
        if not keys:
            return f"Mappa punti ({scope_label}): -"
        sample = [f"{k}={self.point_outcome_map[k]}" for k in keys[:8]]
        suffix = " ..." if len(keys) > 8 else ""
        return f"Mappa punti ({scope_label}): " + " | ".join(sample) + suffix

    def _configure_rx_formation(self):
        # Mostra il dialogo di configurazione formazioni ricezione
        dialog = QDialog(self)
        dialog.setWindowTitle("Configura formazioni ricezione")
        dialog.setMinimumWidth(750)
        dialog.setMinimumHeight(520)

        layout = QVBoxLayout(dialog)

        cfg = self._load_rx_formation_config("global")
        if not cfg and self.current_context:
            for side in ("home", "away"):
                team = self.current_context.get(f"{side}_team", {})
                tid = team.get("id")
                if tid:
                    team_cfg = self._load_rx_formation_config(str(tid))
                    if team_cfg:
                        logger.debug("migrating team config %s to global", tid)
                        cfg = team_cfg
                        break
        if not cfg:
            scheme = "P-S-C"
            if self.current_context:
                scheme = self.current_context.get("game_method", "P-S-C")
            cfg = self.formation_manager.generate_all_rotations(scheme)
        configs = dict(cfg)

        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        top_row.addWidget(QLabel("Rot:"))

        rot_btns = {}
        rot_group = QButtonGroup(page)
        for r in range(1, 7):
            btn = QPushButton(str(r))
            btn.setCheckable(True)
            btn.setFixedSize(34, 30)
            btn.setStyleSheet(
                "QPushButton { font-weight: bold; border-radius: 4px; }"
                "QPushButton:checked { background-color: #3B82F6; color: white; }"
            )
            rot_btns[r] = btn
            rot_group.addButton(btn, r)
            top_row.addWidget(btn)
        rot_btns[1].setChecked(True)

        top_row.addSpacing(12)

        scheme_group = QButtonGroup(page)
        btn_psc = QRadioButton("P-S-C")
        btn_pcs = QRadioButton("P-C-S")
        btn_psc.setChecked(True)
        scheme_group.addButton(btn_psc)
        scheme_group.addButton(btn_pcs)
        top_row.addWidget(btn_psc)
        top_row.addWidget(btn_pcs)

        top_row.addStretch()

        btn_pulisci = QPushButton("Pulisci")
        btn_pulisci.setStyleSheet("QPushButton { color: #DC2626; }")
        top_row.addWidget(btn_pulisci)

        page_layout.addLayout(top_row)

        body_row = QHBoxLayout()

        court = FormationCourtWidget("home", page)
        court.setMinimumSize(280, 280)
        court.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        body_row.addWidget(court, 1)

        page_layout.addLayout(body_row, 1)

        layout.addWidget(page)

        _current_rotation = 1

        def _save_current_rotation(rotation):
            # Salva la rotazione corrente
            nonlocal _current_rotation
            _current_rotation = rotation
            configs[rotation] = court.get_positions()

        def _load_current_rotation(rotation):
            # Carica la rotazione corrente
            court.set_positions(configs.get(rotation, {}))

        def _save_config():
            # Salva la configurazione
            self._save_rx_formation_config(configs, "global")

        def on_rotation(btn_id):
            """Gestisce il cambio rotazione."""
            if btn_id >= 0:
                prev = _current_rotation
                if prev != btn_id:
                    _save_current_rotation(prev)
                _load_current_rotation(btn_id)

        rot_group.idClicked.connect(on_rotation)

        def gen_scheme(scheme):
            """Genera lo schema selezionato."""
            nonlocal _current_rotation
            new_cfg = self.formation_manager.generate_all_rotations(scheme)
            configs.clear()
            configs.update(new_cfg)
            rid = rot_group.checkedId()
            if rid >= 0:
                _current_rotation = rid
            else:
                rid = 1
            _load_current_rotation(rid)
            _save_config()

        btn_psc.clicked.connect(lambda checked: gen_scheme("P-S-C"))
        btn_pcs.clicked.connect(lambda checked: gen_scheme("P-C-S"))

        def on_positions_changed():
            """Gestisce il cambiamento posizioni."""
            rid = rot_group.checkedId()
            if rid >= 0:
                _save_current_rotation(rid)
                _save_config()

        court.positionsChanged.connect(on_positions_changed)

        def on_cell_clicked(nx, ny):
            """Gestisce il click su cella nel campo."""
            rid = rot_group.checkedId()
            if rid < 0:
                return
            menu = QMenu(court)
            for role in self.formation_manager.ROLE_CODES:
                act = menu.addAction(role)
                act.setData(role)
            menu.addSeparator()
            act_clear = menu.addAction("-")
            act_clear.setData(None)
            cx, cy = court._to_canvas(nx, ny)
            action = menu.exec(court.mapToGlobal(QPoint(int(cx), int(cy))))
            if action is None:
                return
            role_data = action.data()
            rd = configs.setdefault(rid, {})
            for old_role in list(rd.keys()):
                ox, oy = rd[old_role]
                if abs(ox - nx) < 0.05 and abs(oy - ny) < 0.05:
                    del rd[old_role]
            if role_data is not None:
                rd[role_data] = (nx, ny)
            court.set_positions(rd)
            _save_config()

        court.cellClicked.connect(on_cell_clicked)

        def on_pulisci():
            """Pulisce la rotazione corrente."""
            rid = rot_group.checkedId()
            if rid >= 0:
                court.clear_positions()
                _save_current_rotation(rid)
                _save_config()

        btn_pulisci.clicked.connect(on_pulisci)

        _load_current_rotation(1)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(dialog.close)
        layout.addWidget(btn_box)

        dialog.exec()

    def open_settings_dialog(self):
        """Apre il dialogo delle impostazioni di scouting."""
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
            """Aggiorna le etichette di anteprima."""
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
            """Gestisce il cambio scope mappa punti."""
            selected = cmb_scope.currentData()
            new_scope = str(selected or "global").strip().lower()
            self.point_outcome_scope = new_scope
            self._save_point_outcome_scope()
            self.point_outcome_map = self._load_point_outcome_map()
            refresh_preview_labels()

        def duplicate_global_rules_to_current_scope():
            """Copia le regole globali nello scope corrente."""
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
            """Esegue un callback e aggiorna le anteprime."""
            callback()
            refresh_preview_labels()

        def on_sync_timer_changed(state: int):
            """Gestisce il cambio sincronizzazione timer."""
            self.sync_timer_with_video = state == int(Qt.CheckState.Checked)
            self._save_timer_sync_with_video()

        chk_sync_timer.stateChanged.connect(on_sync_timer_changed)

        eval_row = QHBoxLayout()
        eval_row.addWidget(QLabel("Codice attacco predefinito:"))
        cmb_attack_eval = QComboBox()
        for code in ["#", "+", "!", "/", "-", "="]:
            cmb_attack_eval.addItem(code, code)
        idx_eval = cmb_attack_eval.findData(self.default_attack_eval)
        if idx_eval >= 0:
            cmb_attack_eval.setCurrentIndex(idx_eval)
        eval_row.addWidget(cmb_attack_eval)
        eval_row.addStretch()
        layout.addLayout(eval_row)

        def on_attack_eval_changed():
            """Gestisce il cambio valutazione attacco predefinita."""
            selected = cmb_attack_eval.currentData()
            self.default_attack_eval = str(selected or "!")
            self._save_default_attack_eval()

        cmb_attack_eval.currentIndexChanged.connect(lambda _i: on_attack_eval_changed())

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

        btn_rx = QPushButton("Configura formazioni ricezione")
        btn_rx.clicked.connect(
            lambda: run_and_refresh(self._configure_rx_formation)
        )
        layout.addWidget(btn_rx)

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
        # Aggiorna l'etichetta della mappa hotkey attiva
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
        # Aggiorna il suggerimento hotkey nella UI
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
        # Applica le modifiche UI per la modalità tastiera
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
        # Gestisce il cambio modalità input tastiera
        if not hasattr(self, "keyboard_mode_selector"):
            return

        selected = self.keyboard_mode_selector.currentData()
        self.keyboard_only_mode = selected == "keyboard"
        self._save_keyboard_mode_enabled()
        self._apply_keyboard_mode_ui()

        if self.keyboard_only_mode and hasattr(self, "code_input"):
            self.code_input.setFocus()

    def _execute_hotkey_action(self, action: str) -> bool:
        # Esegue l'azione associata a un hotkey
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
        # Gestisce la pressione di un tasto funzione
        token = self._qt_key_to_hotkey_token(key)
        if token is None:
            return False

        action = self._active_hotkey_bindings().get(token)
        if not action:
            return False

        return self._execute_hotkey_action(action)

    def _shortcuts_to_text(self, shortcuts: list[tuple[str, str]]) -> str:
        # Converte le scorciatoie in testo modificabile
        rows = [
            "# Una riga per bottone (formato: Etichetta=Token)",
            "# Esempio: Battuta=S",
        ]
        for label, token in shortcuts:
            rows.append(f"{label}={token}")
        return "\n".join(rows)

    def _parse_shortcuts_text(self, text: str) -> list[tuple[str, str]]:
        # Analizza il testo delle scorciatoie
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
        # Salva la configurazione delle scorciatoie
        settings = self._shortcuts_settings()
        serialized = "\n".join(
            f"{label}|{token}" for label, token in self.code_shortcuts
        )
        settings.setValue(self.SHORTCUTS_SETTINGS_KEY, serialized)

    def _load_shortcuts_config(self) -> list[tuple[str, str]]:
        # Carica la configurazione delle scorciatoie
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
        # Ricostruisce i pulsanti delle scorciatoie codice
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
        # Mostra il dialogo di configurazione scorciatoie
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
        # Reimposta le scorciatoie ai valori predefiniti
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
        # Crea un pulsante per il tastierino DataVolley
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
        # Imposta o sostituisce il prefisso squadra nel codice
        if not hasattr(self, "code_input"):
            return

        current = self.code_input.text().strip().upper()
        if current and current[0] in {"A", "B", "*"}:
            current = current[1:]

        self.code_input.setText(f"{prefix}{current}")
        self.code_input.setFocus()
        self.code_input.setCursorPosition(len(self.code_input.text()))

    def _remove_last_code_char(self):
        # Rimuove l'ultimo carattere dal campo codice
        if not hasattr(self, "code_input"):
            return
        current = self.code_input.text()
        self.code_input.setText(current[:-1])
        self.code_input.setFocus()
        self.code_input.setCursorPosition(len(self.code_input.text()))

    def _apply_macro_preset(self, token: str):
        # Applica un preset macro al campo codice
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
        # Crea il tastierino DataVolley nella UI
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
        # Inserisce un token nel campo codice
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
        # Aggiunge un carattere al campo codice
        if not hasattr(self, "code_input"):
            return

        current = self.code_input.text()
        self.code_input.setText(f"{current}{char}")
        self.code_input.setFocus()
        self.code_input.setCursorPosition(len(self.code_input.text()))

    def keyPressEvent(self, event):
        """Gestisce gli eventi di pressione tasti."""
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
            if self._serve_mode_active:
                self._exit_serve_mode()
            if self._attack_mode_active:
                self._exit_attack_mode()
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
        # Restituisce la squadra selezionata per il codice
        if hasattr(self, "code_team_selector"):
            selected = self.code_team_selector.currentData()
            if selected in {"home", "away"}:
                return selected
        return "home"

    def _set_code_team_side(self, side: str):
        # Imposta la squadra selezionata per il codice
        if not hasattr(self, "code_team_selector"):
            return

        idx = self.code_team_selector.findData("away" if side == "away" else "home")
        if idx >= 0:
            self.code_team_selector.setCurrentIndex(idx)

    def _persist_current_match_video_path(self, video_path: str | None):
        # Salva il percorso video nel record match
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
        # Ripristina lo stile predefinito del campo codice
        if hasattr(self, "code_input"):
            self.code_input.setStyleSheet("")

    def _feedback_code_submission(self, success: bool, message: str | None = None):
        # Mostra feedback visivo per l'invio codice
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
        # Restituisce il contesto della squadra indicata
        key = "home_team" if side == "home" else "away_team"
        return self.current_context.get(key, {}) if self.current_context else {}

    def _resolve_player_id(
        self, side: str, player_number: str | int | None
    ) -> int | None:
        # Risolve l'ID giocatore dal numero maglia
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
        # Rimuove l'evidenziazione da tutti i campi
        if hasattr(self, "home_court"):
            self.home_court.clear_highlight()
        if hasattr(self, "away_court"):
            self.away_court.clear_highlight()

    def _highlight_player_on_courts(self, side: str, player_number: str | None):
        # Evidenzia un giocatore sul campo
        self._clear_player_highlight()
        if not player_number:
            return

        if side == "home" and hasattr(self, "home_court"):
            self.home_court.set_highlight_player(player_number)
        elif side == "away" and hasattr(self, "away_court"):
            self.away_court.set_highlight_player(player_number)

    def _populate_court_from_lineup(self):
        import json
        match_id = self.current_context.get("match_id")
        set_number = self.current_context.get("set_number")
        if not match_id or not set_number:
            return
        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchSet
                ms = (
                    session.query(MatchSet)
                    .filter_by(match_id=match_id, set_number=set_number)
                    .first()
                )
                if not ms:
                    return

                home_nums = {} if not ms.home_lineup else json.loads(ms.home_lineup)
                away_nums = {} if not ms.away_lineup else json.loads(ms.away_lineup)

                home_data = self.current_context.setdefault("home_team", {})
                away_data = self.current_context.setdefault("away_team", {})
                home_name = home_data.get("name", "Casa")
                away_name = away_data.get("name", "Trasferta")

                if home_nums:
                    home_data["lineup"] = home_nums
                if away_nums:
                    away_data["lineup"] = away_nums

                logger.info("Popolamento campo: home=%s away=%s",
                           list(home_nums.values()) if home_nums else "vuoto",
                           list(away_nums.values()) if away_nums else "vuoto")
                print(f"[DEBUG] Popolamento campo: home={list(home_nums.values()) if home_nums else 'vuoto'} away={list(away_nums.values()) if away_nums else 'vuoto'}")

                if hasattr(self, "home_court"):
                    self.home_court.update_lineup(home_name, home_nums)
                if hasattr(self, "away_court"):
                    self.away_court.update_lineup(away_name, away_nums)
                self._sync_formation_view()
        except Exception as e:
            logger.exception("Errore popolamento campo da formazione")

    def _ensure_set_with_events(self):
        match_id = self.current_context.get("match_id")
        set_number = int(self.current_context.get("set_number", 1) or 1)
        if not match_id:
            return
        try:
            from sqlalchemy import func
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import ScoutEvent, MatchSet
                cnt = session.query(func.count(ScoutEvent.id)).join(
                    MatchSet, ScoutEvent.set_id == MatchSet.id,
                ).filter(
                    ScoutEvent.match_id == match_id,
                    MatchSet.set_number == set_number,
                    ScoutEvent.special_code == 'SK',
                ).scalar()
                if cnt and cnt > 0:
                    return
                first = session.query(MatchSet.set_number).join(
                    ScoutEvent, ScoutEvent.set_id == MatchSet.id,
                ).filter(
                    ScoutEvent.match_id == match_id,
                    ScoutEvent.special_code == 'SK',
                ).order_by(MatchSet.set_number).first()
                if first:
                    self.current_context["set_number"] = first[0]
                    logger.info("Reindirizzamento al set %d (il set %d non ha eventi)", first[0], set_number)
        except Exception as e:
            logger.exception("Errore _ensure_set_with_events")

    def _apply_point_logic(self, side: str) -> dict:
        # Applica la logica punto e side-out
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
        # Registra un codice DataVolley inserito
        if not self.current_context:
            return

        if not self._require_initial_service_selected():
            return

        raw_code = self.code_input.text().strip() if hasattr(self, "code_input") else ""
        if not raw_code:
            return

        parsed = parse_datavolley_code(raw_code, self.DATA_VOLLEY_SKILL_ALIASES, self.DATA_VOLLEY_EVALUATIONS)
        if parsed.get("team_side") is None:
            parsed["team_side"] = self._selected_code_team_side()
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
        point_side = resolve_point_team_from_evaluation(side, skill, evaluation, self.point_outcome_map, self.DATA_VOLLEY_SKILL_ALIASES)

        snapshot = self._snapshot_state()
        point_result = None
        if point_side is not None:
            point_result = self._apply_point_logic(point_side)
            self._exit_attack_mode()

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

        self.rally_history.append({"snapshot": snapshot, "event_id": event_id})

        history_text = f"{self._format_elapsed()} | {team_name} | {raw_code}"
        score_home = None
        score_away = None
        if point_result is not None:
            score_home = point_result["score_home"]
            score_away = point_result["score_away"]
            history_text = f"{history_text} -> {score_home}-{score_away}"

        set_number = self.current_context.get("set_number")
        self._append_history(
            history_text,
            event_id=event_id,
            kind=history_kind,
            score_home=score_home,
            score_away=score_away,
            set_number=set_number,
        )

        self._refresh_view()
        if event_id is not None:
            self._render_event_on_courts(event_id)
        self._feedback_code_submission(
            True,
            f"Codice registrato: {raw_code}",
        )

        self.code_input.clear()
        self.code_input.setFocus()

        if hasattr(self, "btn_toggle_keypad") and self.btn_toggle_keypad.isChecked():
            self.btn_toggle_keypad.setChecked(False)

    def _is_editing_completed_match(self) -> bool:
        # Verifica se si sta modificando un match terminato
        if not self.current_context:
            return False
        return bool(self.current_context.get("editing_completed_match", False))

    def _set_controls_enabled(self, enabled: bool):
        # Abilita o disabilita i controlli della UI
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
        if hasattr(self, "btn_formazioni"):
            self.btn_formazioni.setEnabled(enabled)

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

        if hasattr(self, "home_team_label"):
            self.home_team_label.setEnabled(enabled)
        if hasattr(self, "away_team_label"):
            self.away_team_label.setEnabled(enabled)

        for btn in self.skill_buttons:
            btn.setEnabled(enabled)
        for btn in self.code_shortcut_buttons:
            btn.setEnabled(enabled)
        for btn in self.code_keypad_buttons:
            btn.setEnabled(enabled)

        self._update_video_layout_controls()

    def _timeout_limit_per_set(self) -> int:
        # Restituisce il limite di timeout per set
        try:
            return max(
                1, int(self.current_context.get("timeout_limit_per_set", 2) or 2)
            )
        except Exception:
            return 2

    def _update_timeout_labels(self):
        # Aggiorna le etichette dei timeout
        limit = self._timeout_limit_per_set()
        self.timeout_home_label.setText(
            f"TO Casa: {self.timeouts_used.get('home', 0)}/{limit}"
        )
        self.timeout_away_label.setText(
            f"TO Ospiti: {self.timeouts_used.get('away', 0)}/{limit}"
        )

    def _format_seconds(self, total_seconds: int) -> str:
        # Formatta i secondi in MM:SS
        minutes = max(0, int(total_seconds)) // 60
        seconds = max(0, int(total_seconds)) % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _format_elapsed(self) -> str:
        # Restituisce il tempo trascorso formattato
        return self._format_seconds(int(max(0.0, float(self.elapsed_seconds_exact))))

    def _reset_timer_ui(self):
        # Reimposta l'interfaccia del timer
        self.timer_label.setText(self._format_elapsed())
        self.btn_timer_toggle.setText("Avvia timer")

    def _on_timer_tick(self):
        # Gestisce il tick del timer
        self.elapsed_seconds_exact = max(0.0, float(self.elapsed_seconds_exact) + 1.0)
        self.elapsed_seconds = int(self.elapsed_seconds_exact)
        self.timer_label.setText(self._format_elapsed())
        self._highlight_history_by_current_time()

    def _toggle_timer(self):
        # Avvia o mette in pausa il timer
        if self.timer_running:
            self.timer.stop()
            self.timer_running = False
            self.btn_timer_toggle.setText("Avvia timer")
        else:
            self.timer.start()
            self.timer_running = True
            self.btn_timer_toggle.setText("Pausa timer")

    def _reset_timer(self):
        # Reimposta il timer a zero
        self.elapsed_seconds_exact = 0.0
        self.elapsed_seconds = 0
        self.timer_label.setText(self._format_elapsed())
        self._highlight_history_by_current_time()

    def _refresh_setter_numbers(self):
        # Aggiorna i numeri dei palleggiatori
        for side in ("home", "away"):
            team_data = self._team_context(side)
            lineup_numbers = {
                normalize_lineup_number(v)
                for v in team_data.get("lineup", {}).values()
                if normalize_lineup_number(v) is not None
            }
            explicit = normalize_lineup_number(team_data.get("setter_number"))
            detected = self.formation_manager.detect_setter_number(
                self.current_context.get("match_id"),
                team_data.get("id"),
                lineup_numbers,
                explicit_setter=explicit,
            )
            if detected is not None:
                self.setter_number_by_side[side] = detected
            else:
                team_id = team_data.get("id")
                if team_id:
                    settings = self._shortcuts_settings()
                    remembered = settings.value(f"setter_memory_{team_id}", "", type=str)
                    if remembered and remembered in lineup_numbers:
                        self.setter_number_by_side[side] = remembered
                        team_data["setter_number"] = remembered
                        continue
                self.setter_number_by_side[side] = self._prompt_for_setter(side)

    def _update_outer_service_hints(self):
        # Aggiorna i suggerimenti servizio esterni
        entries = {
            "home": getattr(self, "home_team_label", None),
            "away": getattr(self, "away_team_label", None),
        }
        for side, label in entries.items():
            if label is None:
                continue

            rotation = self._get_current_rotation(side)
            rotation_str = f"Rot. {rotation}" if rotation is not None else "-"

            team_name = (
                self.current_context.get(f"{side}_team", {}).get("name", "").upper()
                if self.current_context
                else ""
            )

            label.setText(f"{team_name}\n{rotation_str}")
            label.setStyleSheet(
                "font-size: 10px; font-weight: bold; color: #F6EFE9;"
                "border: 1px solid #374151; border-radius: 8px; padding: 6px 4px;"
                "background-color: #4B5563;"
            )

        # Pulsanti BATTUTA laterali
        for side in ("home", "away"):
            btn = getattr(self, f"{side}_battuta_btn", None)
            if btn is None:
                continue
            is_serving = side == self.serving_side
            if is_serving:
                btn.setText("BATTUTA")
                btn.setStyleSheet(
                    "font-size: 10px; font-weight: bold; color: white;"
                    "border: 1px solid #C2410C; border-radius: 8px; padding: 6px 4px;"
                    "background-color: #E95420;"
                )
                btn.setVisible(True)
                self._reception_active = True
                self._serve_mode_active = True
            else:
                btn.setVisible(False)

    def _reset_serve_hint(self):
        """Nasconde il pulsante BATTUTA laterale dopo l'atterraggio."""
        side = self._serve_zone_start_side
        if side is None:
            return
        btn = getattr(self, f"{side}_battuta_btn", None)
        if btn is not None:
            btn.setVisible(False)

    def _update_initial_service_controls(self):
        # Aggiorna i controlli della battuta iniziale
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
        # Imposta la squadra al servizio iniziale
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
        # Richiede la selezione della battuta iniziale
        if self.initial_service_selected:
            return True

        QMessageBox.information(
            self,
            "Battuta iniziale non impostata",
            "Seleziona prima la squadra al servizio a inizio set.",
        )
        return False

    def _cell_to_overlay(self, court, pos_code):
        """Converte il centro di una cella in coordinate dell'overlay."""
        center = court.get_cell_center(pos_code)
        if center is None:
            return None
        return QPointF(
            float(court.x() + center.x()),
            float(court.y() + center.y()),
        )

    def _get_start_overlay_pos(self):
        """Coordinate del punto di partenza (posizione click sul badge) nell'overlay."""
        if self._serve_start_overlay_pos is not None:
            return QPointF(self._serve_start_overlay_pos)
        # Fallback: centro del badge
        side = self._serve_zone_start_side
        badge = self.home_battuta_btn if side == "home" else self.away_battuta_btn
        center = badge.mapTo(self.courts_container, badge.rect().center())
        return QPointF(float(center.x()), float(center.y()))

    def _get_end_overlay_pos(self, side: str, pos_code: str):
        """Coordinate del punto di arrivo nell'overlay (centro cella)."""
        court = self.home_court if side == "home" else self.away_court
        return self._cell_to_overlay(court, pos_code)

    def _get_click_overlay_pos(self, side: str, click_x: float, click_y: float):
        """Coordinate del click sul campo nell'overlay."""
        court = self.home_court if side == "home" else self.away_court
        return QPointF(
            float(court.x() + click_x),
            float(court.y() + click_y),
        )

    def _on_battuta_badge_clicked(self, side: str):
        """Cliccando sul badge BATTUTA attiva la modalità battuta."""
        logger.debug("_on_battuta_badge_clicked side=%s serve_mode_active=%s", side, self._serve_mode_active)
        if not self.current_context:
            return

        if side != self.serving_side:
            return

        if not self._require_initial_service_selected():
            return

        if self._serve_zone_start is not None:
            self._exit_serve_mode()
            self._refresh_view()
            return

        self._exit_attack_mode()

        # P1 corrisponde sempre alla zona 1 (posizione di battuta)
        zone_start = "1"

        self._serve_mode_active = True
        self._serve_zone_start = zone_start
        self._serve_zone_start_side = side
        self._serve_zone_end = None
        self._serve_zone_end_side = None

        # Memorizza la posizione del click sul badge
        badge = self.home_battuta_btn if side == "home" else self.away_battuta_btn
        global_pos = QCursor.pos()
        overlay_pos = self.courts_container.mapFromGlobal(global_pos)
        self._serve_start_overlay_pos = QPointF(overlay_pos.x(), overlay_pos.y())

        self._serve_receiver = None
        self._show_reception_eval_buttons(False)

        self.serve_overlay.clear_trajectory()
        self.serve_overlay.setGeometry(self.courts_container.rect())

        serving_team = self.current_context.get(f"{side}_team", {}).get(
            "name", "Casa" if side == "home" else "Ospiti"
        )
        lineup = self._team_context(side).get("lineup", {})
        server_number = normalize_lineup_number(lineup.get("P1")) or ""
        self.subtitle.setText(
            f"Battuta {serving_team}: clicca sul campo per il punto di arrivo"
        )
        self._clear_player_highlight()
        self._highlight_player_on_courts(side, server_number)
        self._refresh_setter_numbers()
        self.home_court.setClickable(True)
        self.away_court.setClickable(True)
        self._update_reception_formation_display()

    def _clear_trajectory_description(self):
        if hasattr(self, "trajectory_desc_label"):
            self.trajectory_desc_label.clear()
            self.trajectory_desc_label.setVisible(False)

    def _show_trajectory_description(self, text: str):
        if not hasattr(self, "trajectory_desc_label"):
            return
        if text:
            self.trajectory_desc_label.setText(text)
            self.trajectory_desc_label.setVisible(True)
        else:
            self._clear_trajectory_description()

    def _exit_serve_mode(self):
        # Esce dalla modalità battuta
        logger.debug("_exit_serve_mode")
        self._reset_serve_hint()
        self._serve_mode_active = False
        self._reception_active = False
        self._update_reception_formation_display()
        self._serve_zone_start = None
        self._serve_zone_start_side = None
        self._serve_zone_end = None
        self._serve_zone_end_side = None
        self._serve_start_overlay_pos = None
        self._serve_receiver = None
        self._show_reception_eval_buttons(False)
        self.home_court.setClickable(False)
        self.away_court.setClickable(False)
        self._clear_player_highlight()
        self._clear_trajectory_description()
        self.serve_overlay.clear_trajectory()
        if self.current_context:
            self.subtitle.setText(
                "Seleziona la battuta iniziale per iniziare lo scouting."
                if not self.initial_service_selected
                else "Pronto per scoutizzare."
            )

    def _toggle_attack_mode(self):
        # Attiva o disattiva la modalità attacco
        if not self.current_context or not self.initial_service_selected:
            return
        self._attack_mode_active = not self._attack_mode_active
        if self._attack_mode_active:
            self._attack_side = None
            self._attack_player = None
            self._attack_start_overlay_pos = None
            self._attack_start_zone = None
            self._attack_end_zone = None
            self._attack_end_side = None
            self.serve_overlay.clear_trajectory()
            self.subtitle.setText("Clicca sul giocatore che attacca")
            self.home_court.setClickable(True)
            self.away_court.setClickable(True)
            self._show_attack_formation()
        else:
            self._exit_attack_mode()

    def _auto_enter_attack_after_reception(self):
        """Dopo una ricezione, entra automaticamente in modalità attacco."""
        if not self.current_context or not self.initial_service_selected:
            return
        self._attack_mode_active = True
        self._attack_side = None
        self._attack_player = None
        self._attack_start_overlay_pos = None
        self._attack_start_zone = None
        self._attack_end_zone = None
        self._attack_end_side = None
        self.serve_overlay.clear_trajectory()
        self.subtitle.setText("Clicca sul giocatore che attacca")
        self.home_court.setClickable(True)
        self.away_court.setClickable(True)
        receiving_side = "away" if self.serving_side == "home" else "home"
        court = self.home_court if receiving_side == "home" else self.away_court
        court.set_reception_positions(None)
        other = self.away_court if receiving_side == "home" else self.home_court
        other.set_reception_positions(None)
        self._show_attack_formation()

    def _exit_attack_mode(self):
        # Esce dalla modalità attacco
        self._clear_attack_formation()
        self._attack_mode_active = False
        self._attack_side = None
        self._attack_player = None
        self._attack_start_overlay_pos = None
        self._attack_start_zone = None
        self._attack_end_zone = None
        self._attack_end_side = None
        self.home_court.setClickable(False)
        self.away_court.setClickable(False)
        self.serve_overlay.clear_trajectory()
        self._show_attack_eval_buttons(False)
        self._clear_trajectory_description()

    def _reset_attack_state(self):
        """Resetta lo stato attacco ma resta in modalità attacco."""
        self._attack_side = None
        self._attack_player = None
        self._attack_start_overlay_pos = None
        self._attack_start_zone = None
        self._attack_end_zone = None
        self._attack_end_side = None
        self._show_attack_eval_buttons(False)
        self.serve_overlay.clear_trajectory()
        self._clear_player_highlight()
        self._clear_trajectory_description()
        self.subtitle.setText("Clicca sul giocatore che attacca")
        self._show_attack_formation()

    def _on_attack_cell_clicked(self, side: str, pos_code: str, zone: str, click_x: float = 0, click_y: float = 0):
        # Gestisce il click su una cella in modalità attacco
        lineup = self._team_context(side).get("lineup", {})
        player = normalize_lineup_number(lineup.get(pos_code))
        if player is None:
            QMessageBox.warning(
                self, "Nessun giocatore",
                "Nessun giocatore in questa posizione.",
            )
            return

        # Fase 4: tutte le fasi complete → auto-submit con eval predefinito e riparti
        if self._attack_player is not None and self._attack_start_zone is not None and self._attack_end_zone is not None:
            self._submit_attack_code(self.default_attack_eval)
            self._reset_attack_state()
            # continua con la Fase 1 usando questo click

        if self._attack_player is None:
            # Fase 1: seleziona attaccante
            self._attack_side = side
            self._attack_player = player
            self._clear_player_highlight()
            self._highlight_player_on_courts(side, player)
            team_name = self.current_context.get(
                f"{side}_team", {}
            ).get("name", "Casa" if side == "home" else "Ospiti")
            self.subtitle.setText(
                f"Attacco {team_name} #{player}: clicca sul punto di partenza"
            )
        elif self._attack_start_zone is None:
            # Fase 2: punto di partenza — deve essere nel campo dell'attaccante
            if side != self._attack_side:
                QMessageBox.warning(
                    self, "Punto di partenza",
                    "Il punto di partenza deve essere nel campo del giocatore selezionato.",
                )
                return
            self._attack_start_zone = zone
            self._attack_start_overlay_pos = self._get_click_overlay_pos(side, click_x, click_y)
            team_name = self.current_context.get(
                f"{self._attack_side}_team", {}
            ).get("name", "Casa" if self._attack_side == "home" else "Ospiti")
            self.subtitle.setText(
                f"Attacco {team_name} #{self._attack_player}: clicca sul punto di arrivo"
            )
        else:
            # Fase 3: punto di arrivo (posizione click sul campo)
            self._attack_end_zone = zone
            self._attack_end_side = side

            end_ov = self._get_click_overlay_pos(side, click_x, click_y)
            if self._attack_start_overlay_pos is not None and end_ov is not None:
                self.serve_overlay.set_trajectory(self._attack_start_overlay_pos, end_ov)

            traj_desc = describe_trajectory(self._attack_start_zone, self._attack_end_zone, "A")
            self._show_trajectory_description(f"Attacco: {traj_desc}" if traj_desc else "")

            self.subtitle.setText("Scegli la valutazione dell'attacco")
            self._show_attack_eval_buttons(True)

    def _show_attack_eval_buttons(self, visible: bool):
        # Mostra o nasconde i pulsanti valutazione attacco
        for btn in self._attack_eval_buttons:
            btn.setVisible(visible)
        self._attack_eval_label.setVisible(visible)
        if not visible:
            self._attack_eval_label.setText("  Attacco:")

    def _on_attack_eval_clicked(self, eval_code: str):
        # Gestisce il click su un pulsante valutazione attacco
        if not self._attack_mode_active or self._attack_player is None:
            return
        self._submit_attack_code(eval_code)
        self._reset_attack_state()

    def _submit_attack_code(self, evaluation: str):
        # Invia il codice DataVolley per l'attacco
        lineup = self._team_context(self._attack_side).get("lineup", {})
        attacker = normalize_lineup_number(lineup.get(
            find_player_position_in_lineup(lineup, self._attack_player)
        )) or self._attack_player

        code = f"{attacker}A{evaluation}{self._attack_start_zone}{self._attack_end_zone}"
        self._set_code_team_side(self._attack_side)
        self.code_input.setText(code)
        self._register_datavolley_code()

    def _on_court_cell_clicked(self, side: str, pos_code: str, zone: str, click_x: float = 0, click_y: float = 0):
        # Gestisce il click su una cella del campo
        if self._attack_mode_active:
            self._on_attack_cell_clicked(side, pos_code, zone, click_x, click_y)
            return
        """Fase 1: zona d'arrivo. Fase 2: selezione ricevitore."""
        if not self._serve_mode_active:
            return

        if self._serve_zone_end is None:
            logger.debug("Phase 1: serve arrival zone pos_code=%s zone=%s side=%s", pos_code, zone, side)
            self._serve_zone_end = zone
            self._serve_zone_end_side = side

            self._reset_serve_hint()

            start_ov = self._get_start_overlay_pos()
            end_ov = self._get_click_overlay_pos(side, click_x, click_y)
            if start_ov is not None and end_ov is not None:
                self.serve_overlay.set_trajectory(start_ov, end_ov)

            # Mostra descrizione traiettoria
            traj_desc = describe_trajectory(self._serve_zone_start, self._serve_zone_end, "S")
            self._show_trajectory_description(f"Battuta: {traj_desc}" if traj_desc else "")

            # Se la battuta cade nel campo del battitore → errore battuta, punto agli avversari
            if side == self.serving_side:
                self._submit_serve_error()
                self._exit_serve_mode()
                return

            receiving_side = "away" if self.serving_side == "home" else "home"
            team_name = self.current_context.get(
                f"{receiving_side}_team", {}
            ).get("name", "Ospiti" if receiving_side == "away" else "Casa")
            self.subtitle.setText(
                f"Seleziona il ricevitore cliccando sul campo di {team_name}"
            )
            return

        # --- Fase 2: selezione ricevitore (solo sul campo della squadra in ricezione) ---
        receiving_side = "away" if self.serving_side == "home" else "home"
        if side != receiving_side:
            return

        lineup = self._team_context(side).get("lineup", {})
        receiver_number = normalize_lineup_number(lineup.get(pos_code))
        logger.debug("Phase 2: receiver selection pos_code=%s zone=%s receiver=%s", pos_code, zone, receiver_number)
        if receiver_number is None:
            QMessageBox.warning(
                self, "Nessun giocatore",
                "Nessun giocatore in questa posizione. Seleziona una cella con un giocatore.",
            )
            return

        self._serve_receiver = receiver_number
        self.subtitle.setText(
            f"Ricevitore #{receiver_number} in zona {zone}: scegli la valutazione"
        )
        self._show_reception_eval_buttons(True)

    def _show_reception_eval_buttons(self, visible: bool):
        # Mostra o nasconde i pulsanti valutazione ricezione
        self._eval_label.setVisible(visible)
        for btn in self._reception_eval_buttons:
            btn.setVisible(visible)

    def _on_reception_eval_clicked(self, eval_code: str):
        # Gestisce il click su un pulsante valutazione ricezione
        logger.debug("_on_reception_eval_clicked code=%s receiver=%s", eval_code, self._serve_receiver)
        if not self._serve_mode_active or self._serve_receiver is None:
            return

        if eval_code == "=":
            self._submit_serve_and_reception(
                self._serve_receiver, "=", "#"
            )
            self._exit_serve_mode()
            self._refresh_view()
        else:
            serve_eval = {"#": "-", "-": "+", "+": "-"}.get(eval_code, "-")
            self._submit_serve_and_reception(
                self._serve_receiver, eval_code, serve_eval
            )
            self._exit_serve_mode()
            self._auto_enter_attack_after_reception()

    def _submit_ace_serve(self):
        """Battuta ace: invia solo S#, niente codice ricezione separato."""
        serving_lineup = self._team_context(self.serving_side).get("lineup", {})
        server_number = normalize_lineup_number(serving_lineup.get("P1")) or ""
        code = f"{server_number}S#{self._serve_zone_start}{self._serve_zone_end}"
        self._set_code_team_side(self.serving_side)
        self.code_input.setText(code)
        self._register_datavolley_code()

    def _submit_serve_error(self):
        """Battuta in rete o fuori: invia S=, punto agli avversari."""
        serving_lineup = self._team_context(self.serving_side).get("lineup", {})
        server_number = normalize_lineup_number(serving_lineup.get("P1")) or ""
        code = f"{server_number}S={self._serve_zone_start}{self._serve_zone_end}"
        self._set_code_team_side(self.serving_side)
        self.code_input.setText(code)
        self._register_datavolley_code()

    def _submit_serve_and_reception(self, receiver_number: str, reception_eval: str, serve_eval: str):
        """Registra sia la battuta (S) che la ricezione (R) con la valutazione data.

        Per R# (ricezione perfetta), assegna il punto alla squadra ricevente tramite
        resolve_point_team_from_evaluation.
        """
        serving_lineup = self._team_context(self.serving_side).get("lineup", {})
        server_number = normalize_lineup_number(serving_lineup.get("P1")) or ""

        serving_side = self.serving_side
        receiving_side = "away" if serving_side == "home" else "home"

        serve_code = f"{server_number}S{serve_eval}{self._serve_zone_start}{self._serve_zone_end}"
        reception_code = f"{receiver_number}R{reception_eval}{self._serve_zone_end}{self._serve_zone_end}"

        # Snapshot BEFORE any changes
        snapshot = self._snapshot_state()

        # 1) Register serve event (no point for S-)
        self._set_code_team_side(serving_side)
        parsed_serve = parse_datavolley_code(
            serve_code, self.DATA_VOLLEY_SKILL_ALIASES, self.DATA_VOLLEY_EVALUATIONS
        )
        if parsed_serve.get("team_side") is None:
            parsed_serve["team_side"] = serving_side

        serve_event_id = self._persist_event(
            team_side=serving_side,
            player_id=self._resolve_player_id(serving_side, parsed_serve.get("player_number")),
            skill=parsed_serve.get("skill"),
            evaluation=parsed_serve.get("evaluation"),
            notes=f"Battuta: {serve_code}",
            kind=self.HISTORY_KIND_SKILL,
            zone_start=parsed_serve.get("zone_start"),
            zone_end=parsed_serve.get("zone_end"),
        )
        self.rally_history.append({"snapshot": deepcopy(snapshot), "event_id": serve_event_id})
        self._append_history(
            f"{self._format_elapsed()} | {self._team_name(serving_side)} | {serve_code}",
            event_id=serve_event_id,
            kind=self.HISTORY_KIND_SKILL,
        )

        # 2) Register reception event
        self._set_code_team_side(receiving_side)
        parsed_recv = parse_datavolley_code(
            reception_code, self.DATA_VOLLEY_SKILL_ALIASES, self.DATA_VOLLEY_EVALUATIONS
        )
        if parsed_recv.get("team_side") is None:
            parsed_recv["team_side"] = receiving_side

        point_side: str | None = resolve_point_team_from_evaluation(
            receiving_side,
            parsed_recv.get("skill"),
            parsed_recv.get("evaluation"),
            self.point_outcome_map,
            self.DATA_VOLLEY_SKILL_ALIASES,
        )

        # Snapshot BEFORE point logic (for undo)
        pre_point_snapshot = self._snapshot_state()

        point_result = None
        if point_side is not None:
            point_result = self._apply_point_logic(point_side)

        recv_event_id = self._persist_event(
            team_side=receiving_side,
            player_id=self._resolve_player_id(receiving_side, parsed_recv.get("player_number")),
            skill=parsed_recv.get("skill"),
            evaluation=parsed_recv.get("evaluation"),
            notes=f"Ricezione: {reception_code}"
            + (f" | Punto {point_result['team_name']}" if point_result else ""),
            kind=self.HISTORY_KIND_POINT if point_result else self.HISTORY_KIND_SKILL,
            zone_start=parsed_recv.get("zone_start"),
            zone_end=parsed_recv.get("zone_end"),
        )

        self.rally_history.append({"snapshot": pre_point_snapshot, "event_id": recv_event_id})

        score_text = (
            f" -> {point_result['score_home']}-{point_result['score_away']}"
            if point_result
            else ""
        )
        self._append_history(
            f"{self._format_elapsed()} | {self._team_name(receiving_side)} | {reception_code}{score_text}",
            event_id=recv_event_id,
            kind=self.HISTORY_KIND_POINT if point_result else self.HISTORY_KIND_SKILL,
        )

        self.subtitle.setText(
            f"Battuta {serve_code} | Ricezione {reception_code}"
            + (f" | Punto {point_result['team_name']}" if point_result else "")
        )
        self._refresh_view()
        self.code_input.clear()
        self.code_input.setFocus()

    def _team_name(self, side: str) -> str:
        # Restituisce il nome della squadra per il lato
        if not self.current_context:
            return "Casa" if side == "home" else "Ospiti"
        return self.current_context.get(
            f"{side}_team", {}
        ).get("name", "Casa" if side == "home" else "Ospiti")

    def _open_formation_editor(self):
        # Apre l'editor formazioni ricezione
        from volleyball_scout.ui.formation_editor import FormationEditorDialog

        if not self.current_context:
            return

        # Solo la squadra in ricezione (quella che NON batte)
        side = "away" if self.serving_side == "home" else "home"
        logger.debug("_open_formation_editor side=%s serving_side=%s", side, self.serving_side)
        team_name = self.current_context.get(f"{side}_team", {}).get(
            "name", "Ospiti" if side == "away" else "Casa"
        )
        line_numbers = lineup_numbers_for_side(self._team_context(side).get("lineup", {}))
        if not line_numbers:
            return

        formations = self._formations_by_rotation.get(side, {})
        logger.debug("existing formations for %s: %s", side, sorted(formations.keys()) if formations else "{}")
        dialog = FormationEditorDialog(
            team_name=team_name,
            team_side=side,
            players=line_numbers,
            formations=formations,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._formations_by_rotation[side] = dialog.get_formations()
            logger.debug("formations saved for %s: rotations=%s",
                          side, sorted(self._formations_by_rotation[side].keys()))
            if self.current_context.get("match_id") and self.current_context.get("set_number"):
                self.formation_manager.save_formations(
                    side,
                    self.current_context.get("match_id"),
                    self.current_context.get("set_number"),
                    self._formations_by_rotation.get(side, {}),
                )

        self._update_outer_service_hints()
        self._update_reception_formation_display()

    def _get_current_rotation(self, side: str) -> int | None:
        """Restituisce la rotazione corrente (1-6) per la squadra indicata."""
        lineup = self._team_context(side).get("lineup", {})
        setter = self.setter_number_by_side.get(side)
        if setter is None:
            return None
        from volleyball_scout.core.rotation import get_current_rotation
        return get_current_rotation(lineup, setter)

    def _prompt_for_setter(self, side: str) -> str | None:
        """Chiede all'utente chi è il palleggiatore se non è già registrato."""
        team_name = (
            self.current_context.get(f"{side}_team", {}).get("name", "Casa" if side == "home" else "Ospiti")
            if self.current_context
            else ("Casa" if side == "home" else "Ospiti")
        )
        lineup = self._team_context(side).get("lineup", {})
        player_numbers = sorted(
            set(
                normalize_lineup_number(v)
                for v in lineup.values()
                if normalize_lineup_number(v) is not None
            )
        )
        if not player_numbers:
            return None

        number, ok = QInputDialog.getItem(
            self, f"Palleggiatore {team_name}",
            f"Chi è il palleggiatore di {team_name}?",
            [f"#{n}" for n in player_numbers],
            editable=False,
        )
        if ok and number:
            number = number.lstrip("#")
            self.setter_number_by_side[side] = number
            team_id = self._team_context(side).get("id")
            if team_id:
                settings = self._shortcuts_settings()
                settings.setValue(f"setter_memory_{team_id}", number)
            return number
        return None

    def _show_attack_formation(self):
        # Mostra la formazione di attacco sul campo
        if not self.current_context or not self._attack_mode_active:
            return
        attacking_side = "away" if self.serving_side == "home" else "home"
        self._apply_scheme_formation(attacking_side)

    def _apply_scheme_formation(self, side: str):
        # Applica la formazione schema per la rotazione
        court = self.home_court if side == "home" else self.away_court
        rotation = self._get_current_rotation(side)
        if rotation is None:
            court.set_positions(None)
            return
        team_id = self._team_context(side).get("id")
        method_by_team = self.current_context.get("game_method_by_team", {})
        scheme = method_by_team.get(str(team_id), "P-S-C")
        formation = self.formation_manager.generate_formation_from_scheme(scheme, rotation)
        lineup_raw = self._team_context(side).get("lineup", {})
        lineup = {
            pos: normalize_lineup_number(num)
            for pos, num in lineup_raw.items()
            if normalize_lineup_number(num) is not None
        }
        libero_num = normalize_lineup_number(self._team_context(side).get("libero"))
        roles = self.formation_manager.get_player_roles(
            self.current_context.get("match_id"), team_id
        )
        setter_num = self.setter_number_by_side.get(side)
        player_role_map = self.formation_manager._map_players_to_role_codes(
            lineup, roles, libero_num, known_setter=setter_num
        )
        role_to_player = {v: k for k, v in player_role_map.items()}
        positions = {}
        for role_code, xy in formation.items():
            player_num = role_to_player.get(role_code)
            if player_num:
                positions[player_num] = xy
        if len(positions) < 5:
            court.set_reception_positions(None)
            return
        if side == "away":
            positions = {k: (1.0 - v[0], 1.0 - v[1]) for k, v in positions.items()}
        court.set_reception_positions(positions)

    def _clear_attack_formation(self):
        # Pulisce le formazioni di attacco dai campi
        self.home_court.set_reception_positions(None)
        self.away_court.set_reception_positions(None)

    def _update_reception_formation_display(self):
        """Disegna le formazioni di ricezione sui campi."""
        if not self.current_context:
            logger.debug("update_reception_formation_display: no context")
            return

        logger.debug("update_reception_formation_display serve_mode=%s reception_active=%s serving=%s",
                      self._serve_mode_active, self._reception_active, self.serving_side)

        if not self._reception_active and (self._attack_mode_active or not self._serve_mode_active):
            self.home_court.set_reception_positions(None)
            self.away_court.set_reception_positions(None)
            return

        self._clear_attack_formation()

        for side in ("home", "away"):
            court = self.home_court if side == "home" else self.away_court
            if side == self.serving_side:
                court.set_reception_positions(None)
                continue
            rotation = self._get_current_rotation(side)
            if rotation is None:
                court.set_reception_positions(None)
                self.reception_rotation_hint[side] = "-"
                continue

            self.reception_rotation_hint[side] = str(rotation)
            logger.debug("%s rotation=%s", side, rotation)

            formations = self._formations_by_rotation.get(side, {})
            logger.debug("%s saved formations keys=%s", side, sorted(formations.keys()) if formations else "{}")
            positions = formations.get(rotation)
            if positions:
                logger.debug("%s using saved formation for rot %s: %s", side, rotation, positions)
                first_key = next(iter(positions), None)
                if first_key is not None and not first_key.lstrip("-").isdigit():
                    lineup_raw = self._team_context(side).get("lineup", {})
                    lineup = {
                        pos: normalize_lineup_number(num)
                        for pos, num in lineup_raw.items()
                        if normalize_lineup_number(num) is not None
                    }
                    libero_num = normalize_lineup_number(self._team_context(side).get("libero"))
                    setter_num = self.setter_number_by_side.get(side)
                    team_id = self._team_context(side).get("id")
                    roles = self.formation_manager.get_player_roles(
                        self.current_context.get("match_id"), team_id
                    )
                    player_role_map = self.formation_manager._map_players_to_role_codes(
                        lineup, roles, libero_num, known_setter=setter_num
                    )
                    role_to_player = {v: k for k, v in player_role_map.items()}
                    converted = {}
                    for key, xy in positions.items():
                        player_num = role_to_player.get(key, key)
                        converted[player_num] = xy
                    if len(converted) >= 5:
                        court.set_reception_positions(converted)
                        continue
                else:
                    court.set_reception_positions(positions)
                    continue

            lineup_raw = self._team_context(side).get("lineup", {})
            lineup = {
                pos: normalize_lineup_number(num)
                for pos, num in lineup_raw.items()
                if normalize_lineup_number(num) is not None
            }
            logger.debug("%s lineup=%s", side, lineup)
            setter_number = self.setter_number_by_side.get(side)
            team_id = self._team_context(side).get("id")
            roles = self.formation_manager.get_player_roles(
                self.current_context.get("match_id"), team_id
            )
            logger.debug("%s setter=%s roles=%s", side, setter_number, roles)
            libero_number = normalize_lineup_number(
                self._team_context(side).get("libero")
            )
            rx_config = self._rx_formation_for_side(side)
            if not rx_config:
                default_scheme = "P-S-C"
                team_id = self._team_context(side).get("id")
                if team_id:
                    method_by_team = self.current_context.get("game_method_by_team", {})
                    default_scheme = method_by_team.get(str(team_id), "P-S-C")
                rx_config = self.formation_manager.generate_all_rotations(default_scheme)
            if rx_config:
                config_positions = self.formation_manager.resolve_formation_player_assignments(
                    lineup, roles, rx_config, rotation, libero_number,
                    known_setter=setter_number,
                )
                if config_positions:
                    pos = config_positions
                    if side == "away":
                        pos = {k: (1.0 - v[0], 1.0 - v[1]) for k, v in pos.items()}
                    logger.debug("%s using rx_config positions rot=%s: %s", side, rotation, pos)
                    court.set_reception_positions(pos)
                    continue
                logger.debug("%s rx_config resolve returned None for rot=%s", side, rotation)

            # Fallback: position by lineup order with setter at zone 2
            lineup_positions = {}
            positions_order = ["P1", "P2", "P3", "P4", "P5", "P6"]
            # zone indices in ZONE_POSITIONS: 0=P1, 1=P2, 2=P3, 3=P4, 4=P5, 5=P6
            # assign setter to zone 2 (index 1), remaining players fill rest in order
            setter_found = False
            player_list = []
            for pc in positions_order:
                pn = lineup.get(pc)
                if pn:
                    if setter_number and pn == setter_number:
                        lineup_positions[pn] = self.formation_manager.ZONE_POSITIONS[1]
                        setter_found = True
                    else:
                        player_list.append(pn)
            if len(player_list) + (1 if setter_found else 0) >= 5:
                remaining_indices = [i for i in range(6) if i != 1]
                for i, pn in enumerate(player_list):
                    if i < len(remaining_indices):
                        lineup_positions[pn] = self.formation_manager.ZONE_POSITIONS[remaining_indices[i]]
                pos = lineup_positions
                if side == "away":
                    pos = {k: (1.0 - v[0], 1.0 - v[1]) for k, v in pos.items()}
                logger.debug("%s using lineup-order fallback: %s", side, pos)
                court.set_reception_positions(pos)
                continue

            game_method_by_team = self.current_context.get("game_method_by_team", {})
            auto_positions = self.formation_manager.auto_generate_reception_positions(
                lineup, setter_number, roles, team_id, game_method_by_team, libero_number
            )
            if auto_positions:
                pos = auto_positions
                if side == "away":
                    pos = {k: (1.0 - v[0], 1.0 - v[1]) for k, v in pos.items()}
                logger.debug("%s using auto-generation: %s", side, pos)
                court.set_reception_positions(pos)
            elif self.reception_manual_positions.get(side):
                logger.debug("%s using manual positions: %s", side, self.reception_manual_positions[side])
                court.set_reception_positions(self.reception_manual_positions[side])
            else:
                logger.debug("%s no positions available, clearing", side)
                court.set_reception_positions(None)

    def _position_reception_with_prompt(self):
        # Posiziona la ricezione con dialogo di scelta
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
        players = lineup_numbers_for_side(self._team_context(side).get("lineup", {}))
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
        if self.current_context is not None:
            self.formation_manager.save_reception_positions(
                side,
                self.current_context.get("match_id"),
                self.current_context.get("set_number"),
                self.reception_manual_positions[side],
                self._shortcuts_settings(),
                self.RECEPTION_MEMORY_SETTINGS_PREFIX,
            )
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
        # Determina il lato al servizio dal contesto
        away_id = context.get("away_team", {}).get("id")
        serving_team_id = context.get("serving_team_id")

        if serving_team_id is not None and serving_team_id == away_id:
            return "away"
        return "home"

    def _apply_serving_side(self, side: str):
        # Applica il lato al servizio
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
        lineup = dict(team_data.get("lineup", {}))

        # Auto-revert libero se la rotazione lo porterebbe in prima linea
        reverted = self._auto_revert_libero_if_needed(side, lineup)

        rotated = rotate_lineup_clockwise(lineup)
        team_data["lineup"] = rotated
        self._save_lineups_to_db()

    def _auto_revert_libero_if_needed(self, side: str, lineup: dict) -> bool:
        """Reverta il libero se dopo la rotazione finirebbe in prima linea. Restituisce True se ha revertato."""
        if self._libero_active_player.get(side) is None:
            return False

        libero_num = normalize_lineup_number(
            self.current_context.get(f"{side}_team", {}).get("libero")
        )
        if libero_num is None:
            return False

        current_pos = None
        for pos_code, num in lineup.items():
            if normalize_lineup_number(num) == libero_num:
                current_pos = pos_code
                break
        if current_pos is None:
            return False

        rotation_map = {
            "P1": "P6", "P2": "P1", "P3": "P2",
            "P4": "P3", "P5": "P4", "P6": "P5",
        }
        new_pos = rotation_map.get(current_pos)
        if new_pos is None:
            return False

        front_row = ("P2", "P3", "P4")
        if new_pos not in front_row:
            return False

        replaced_player = self._libero_active_player.get(side)
        lineup[current_pos] = replaced_player
        self._libero_active_player[side] = None

        team_name = self.current_context.get(f"{side}_team", {}).get("name", "")
        note = f"Libero {team_name}: rientro automatico #{replaced_player} (rotazione)"
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
        self._flash_cell(side, current_pos)
        return True

    def _flash_cell(self, side: str, pos_code: str):
        """Lampeggia una cella per 1 secondo."""
        court = self.home_court if side == "home" else self.away_court
        if hasattr(court, "flash_position"):
            court.flash_position(pos_code)

    def _align_lineup_to_server(self, side: str, player_number: str):
        """Ruota la lineup del battitore finché non è in P1; allinea anche la ricevente
        in base al suo ultimo servizio."""
        from volleyball_scout.core.rotation import rotate_lineup_clockwise

        # --- Allinea squadra al servizio (battitore in P1) ---
        team_key = "home_team" if side == "home" else "away_team"
        team_data = self.current_context.get(team_key, {})
        lineup = dict(team_data.get("lineup", {}))
        if lineup:
            pn = str(player_number).strip()
            current_pos = None
            for pos_code, num in lineup.items():
                if str(num).strip() == pn:
                    current_pos = pos_code
                    break
            if current_pos is not None and current_pos != "P1":
                pos_number = int(current_pos[1])
                rotations = (pos_number - 1) % 6
                for _ in range(rotations):
                    lineup = rotate_lineup_clockwise(lineup)
                team_data["lineup"] = lineup

        # --- Allinea squadra che riceve (ultimo battitore in P6) ---
        receiving_side = "away" if side == "home" else "home"
        self._align_receiving_team(receiving_side)

        self._save_lineups_to_db()
        self._refresh_view()

    def _align_receiving_team(self, side: str):
        """Allinea la squadra che riceve: l'ultimo battitore deve stare in P6."""
        try:
            if not self.db or not self.current_context:
                return
            match_id = self.current_context.get("match_id")
            set_number = int(self.current_context.get("set_number", 1))
            if not match_id:
                return
            team_code = "a" if side == "home" else "b"
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import ScoutEvent, Player
                last_serve = (
                    session.query(ScoutEvent)
                    .join(Player, ScoutEvent.player_id == Player.id)
                    .filter(
                        ScoutEvent.match_id == match_id,
                        ScoutEvent.team_side == team_code,
                        ScoutEvent.skill == "S",
                        ScoutEvent.player_id.isnot(None),
                    )
                    .order_by(ScoutEvent.id.desc())
                    .first()
                )
                if not last_serve or not last_serve.player:
                    return
                last_server_num = str(last_serve.player.number).strip()
            team_key = "home_team" if side == "home" else "away_team"
            team_data = self.current_context.get(team_key, {})
            lineup = dict(team_data.get("lineup", {}))
            if not lineup:
                return
            current_pos = None
            for pos_code, num in lineup.items():
                if str(num).strip() == last_server_num:
                    current_pos = pos_code
                    break
            if current_pos is None or current_pos == "P6":
                return
            from volleyball_scout.core.rotation import rotate_lineup_clockwise
            pos_number = int(current_pos[1])
            rotations = pos_number % 6
            for _ in range(rotations):
                lineup = rotate_lineup_clockwise(lineup)
            team_data["lineup"] = lineup
        except Exception as e:
            logger.exception("Errore _align_receiving_team")

    def _snapshot_state(self) -> dict:
        # Cattura lo stato corrente per undo
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
        # Ripristina uno stato precedente
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

    def _save_lineups_to_db(self):
        if self.db is None or not self.current_context:
            return
        import json
        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchSet
                match_id = self.current_context.get("match_id")
                set_number = int(self.current_context.get("set_number", 1))
                set_record = (
                    session.query(MatchSet)
                    .filter_by(match_id=match_id, set_number=set_number)
                    .first()
                )
                if set_record is not None:
                    home_lu = self.current_context.get("home_team", {}).get("lineup", {})
                    away_lu = self.current_context.get("away_team", {}).get("lineup", {})
                    set_record.home_lineup = json.dumps(home_lu) if home_lu else None
                    set_record.away_lineup = json.dumps(away_lu) if away_lu else None
        except Exception as e:
            print(f"⚠️ Errore salvataggio lineups: {e}")

    def _save_set_scores(self):
        if self.db is None or not self.current_context:
            return
        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchSet
                match_id = self.current_context.get("match_id")
                set_number = int(self.current_context.get("set_number", 1))
                set_record = (
                    session.query(MatchSet)
                    .filter_by(match_id=match_id, set_number=set_number)
                    .first()
                )
                if set_record is not None:
                    set_record.score_home = int(self.current_context.get("score_home", 0))
                    set_record.score_away = int(self.current_context.get("score_away", 0))
        except Exception as e:
            print(f"⚠️ Errore salvataggio punteggio set: {e}")

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

                rot = self._get_current_rotation(team_side) if team_side else None
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
                    rotation=rot,
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
        # Normalizza il tipo di storico evento
        kind_upper = str(kind or self.HISTORY_KIND_SYSTEM).upper()
        if kind_upper in {
            self.HISTORY_KIND_POINT,
            self.HISTORY_KIND_SKILL,
            self.HISTORY_KIND_SYSTEM,
        }:
            return kind_upper
        return self.HISTORY_KIND_SYSTEM

    def _matches_history_filter(self, kind: str) -> bool:
        # Verifica se un evento corrisponde al filtro
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
        # Estrae la nota dal testo storico
        parts = str(text or "").split("|", 1)
        if len(parts) == 2:
            return parts[1].strip()
        return str(text or "").strip()

    def _timestamp_from_history_text(self, text: str) -> float | None:
        # Estrae il timestamp dal testo storico
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
        # Compone il testo storico con timestamp
        if timestamp_seconds is None:
            return str(note or "")
        return (
            f"{self._format_seconds(int(max(0.0, float(timestamp_seconds))))} | "
            f"{str(note or '').strip()}"
        )

    def _history_timestamp_from_record(self, record: dict) -> float | None:
        # Restituisce il timestamp da un record storico
        value = record.get("timestamp_seconds")
        if value is not None:
            try:
                return float(max(0.0, float(value)))
            except Exception:
                pass
        return self._timestamp_from_history_text(record.get("text", ""))

    def _set_record_timestamp(self, record: dict, timestamp_seconds: float):
        # Imposta il timestamp su un record storico
        ts = float(max(0.0, float(timestamp_seconds)))
        note = self._extract_note_from_history_text(record.get("text", ""))
        record["timestamp_seconds"] = ts
        record["text"] = self._compose_history_text(note, ts)

    def _current_reference_seconds(self) -> float:
        # Restituisce i secondi di riferimento correnti
        if self.video_timestamp_seconds is not None:
            try:
                return float(max(0.0, float(self.video_timestamp_seconds)))
            except Exception:
                pass
        return float(max(0.0, float(self.elapsed_seconds_exact)))

    def _event_item_timestamp(self, item: QTableWidgetItem | None) -> float | None:
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
        # Trova l'indice del record storico per ID evento
        if event_id is None:
            return -1

        for idx, record in enumerate(self.history_records):
            if record.get("event_id") == event_id:
                return idx
        return -1

    def _highlight_history_by_current_time(self, scroll_to_active: bool = True):
        if not hasattr(self, "events_list"):
            return

        list_count = self.events_list.rowCount()
        if list_count <= 0:
            self.active_history_event_id = None
            return

        reference_seconds = self._current_reference_seconds()
        best_row = -1
        best_ts = -1.0

        for row in range(list_count):
            item = self.events_list.item(row, 0)
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
            for col in range(self.events_list.columnCount()):
                item = self.events_list.item(row, col)
                if item is None:
                    continue
                if row == best_row:
                    active_item = self.events_list.item(row, 0)
                    item.setBackground(QColor("#B45309"))
                    item.setForeground(QColor("#FFF7ED"))
                    fnt = item.font()
                    fnt.setBold(True)
                    item.setFont(fnt)
                else:
                    item.setBackground(QColor(0, 0, 0, 0))
                    item.setForeground(QColor("#D9CFC5"))
                    fnt = item.font()
                    fnt.setBold(False)
                    item.setFont(fnt)

        active_item = self.events_list.item(best_row, 0) if best_row >= 0 else None
        if active_item is None:
            self.active_history_event_id = None
            return

        current_event_id = active_item.data(Qt.ItemDataRole.UserRole)
        self.active_history_event_id = (
            int(current_event_id) if current_event_id is not None else None
        )

        if self.active_history_event_id is not None and self.active_history_event_id != previous_event_id:
            self._render_event_on_courts(self.active_history_event_id)
            if scroll_to_active:
                self.events_list.scrollToItem(
                    active_item,
                    QAbstractItemView.ScrollHint.PositionAtCenter,
                )

    def _seek_video_to_timestamp(self, seconds: float | None):
        # Cerca il video al timestamp specificato
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

    def _on_event_cell_double_clicked(self, row: int, col: int):
        item = self.events_list.item(row, 0)
        if item is None:
            return
        event_id = item.data(Qt.ItemDataRole.UserRole)
        ts = self._event_item_timestamp(item)
        self._seek_video_to_timestamp(ts)
        self.events_list.scrollToItem(
            item, QAbstractItemView.ScrollHint.PositionAtCenter
        )
        if event_id is not None:
            self._restore_event_state(event_id)
            self._render_event_on_courts(event_id)

    def _restore_event_state(self, event_id: int):
        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import ScoutEvent
                event = session.query(ScoutEvent).filter_by(id=int(event_id)).first()
                if not event:
                    return
                ts = float(max(0.0, float(event.video_timestamp or 0.0)))
                self.elapsed_seconds = int(ts)
                self.elapsed_seconds_exact = ts
                self.timer_label.setText(self._format_elapsed())
                sh = int(event.score_home or 0)
                sa = int(event.score_away or 0)
                self.current_context["score_home"] = sh
                self.current_context["score_away"] = sa
                self.home_score.setText(str(sh))
                self.away_score.setText(str(sa))
        except Exception as e:
            logger.exception("Errore restore evento")

    def _render_event_on_courts(self, event_id: int):
        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import ScoutEvent, Player
                event = session.query(ScoutEvent).filter_by(id=int(event_id)).first()
                if not event:
                    return

                side = "home" if event.team_side == "a" else "away"
                self._clear_player_highlight()
                self.serve_overlay.clear_trajectory()

                player_number = None
                if event.player_id:
                    player = session.query(Player).filter_by(id=event.player_id).first()
                    if player:
                        player_number = str(player.number)
                        self._highlight_player_on_courts(side, player_number)

                traj_color = self._eval_to_color(event.evaluation)
                desc = self._describe_event(event)
                rot = getattr(event, "rotation", None) or ""
                rot_str = f" (Rot. {rot})" if rot else ""
                self.subtitle.setText(
                    f"{desc} | #{player_number or '?'}{rot_str}"
                )

                start_zone = event.zone_start
                end_zone = event.zone_end

                skill_letter = str(event.skill or "") if hasattr(event, "skill") else ""
                traj_text = describe_trajectory(start_zone, end_zone, skill_letter)
                self._show_trajectory_description(traj_text)

                if start_zone and start_zone.isdigit() and end_zone and end_zone.isdigit():
                    self.serve_overlay.setGeometry(self.courts_container.rect())
                    opposite = "away" if side == "home" else "home"
                    start_pos = self._zone_to_overlay(side, start_zone)
                    end_pos = self._zone_to_overlay(opposite, end_zone)
                    if start_pos and end_pos:
                        self.serve_overlay.set_trajectory(start_pos, end_pos, color=traj_color)
                elif start_zone and start_zone.isdigit():
                    self.serve_overlay.setGeometry(self.courts_container.rect())
                    start_pos = self._zone_to_overlay(side, start_zone)
                    if start_pos:
                        self.serve_overlay.set_trajectory(start_pos, start_pos, color=traj_color)
                elif end_zone and end_zone.isdigit():
                    self.serve_overlay.setGeometry(self.courts_container.rect())
                    opposite = "away" if side == "home" else "home"
                    end_pos = self._zone_to_overlay(opposite, end_zone)
                    if end_pos:
                        self.serve_overlay.set_trajectory(end_pos, end_pos, color=traj_color)

                # Allinea la lineup al servitore per eventi di battuta
                if event.skill == "S" and player_number:
                    self._align_lineup_to_server(side, player_number)

        except Exception as e:
            logger.exception("Errore rendering evento sul campo")

    ZONE_MAP = {"7": "P4", "8": "P3", "9": "P2"}

    SKILL_NAMES = {"S": "Battuta", "R": "Ricezione", "E": "Alzata", "A": "Attacco", "B": "Muro", "D": "Difesa", "F": "Freeball"}
    EVAL_LABELS = {"#": "perfetto", "+": "buono", "!": "impreciso", "-": "negativo", "=": "errore", "/": "muro"}

    def _zone_to_overlay(self, side: str, zone: str) -> QPointF | None:
        court = self.home_court if side == "home" else self.away_court
        pos = self.ZONE_MAP.get(zone, f"P{zone}")
        return self._cell_to_overlay(court, pos)

    def _eval_to_color(self, evaluation: str | None) -> str:
        return {
            "#": "#22C55E", "+": "#86EFAC", "!": "#EAB308",
            "-": "#F97316", "=": "#EF4444", "/": "#EF4444",
        }.get(evaluation, "#EF4444")

    def _describe_event(self, event) -> str:
        skill_name = self.SKILL_NAMES.get(event.skill, "Evento")
        eval_label = self.EVAL_LABELS.get(event.evaluation, "")
        parts = [f"{skill_name}"]
        if eval_label:
            parts.append(eval_label)
        return " ".join(parts)

    def _event_timestamp_for_event_id(self, event_id: int | None) -> float | None:
        # Restituisce il timestamp per un ID evento
        if event_id is None:
            return None

        for record in self.history_records:
            if record.get("event_id") == event_id:
                return self._history_timestamp_from_record(record)
        return None

    def _nudge_event_timestamp(self, event_id: int | None, delta_seconds: float):
        # Sposta il timestamp di un evento di delta secondi
        base = self._event_timestamp_for_event_id(event_id)
        if base is None:
            base = self._current_reference_seconds()
        self._update_event_timestamp(
            event_id, max(0.0, float(base) + float(delta_seconds))
        )

    def _update_event_timestamp(self, event_id: int | None, new_seconds: float):
        # Aggiorna il timestamp di un evento
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

    def _insert_code_before_event(self, item: QTableWidgetItem):
        # Inserisce un codice DataVolley prima di un evento
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

        parsed = parse_datavolley_code(raw_code, self.DATA_VOLLEY_SKILL_ALIASES, self.DATA_VOLLEY_EVALUATIONS)
        if parsed.get("team_side") is None:
            parsed["team_side"] = self._selected_code_team_side()
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

        row = self.events_list.row(item)
        code_item = self.events_list.item(row, 0)
        if code_item is None:
            return

        menu = QMenu(self)

        ts = self._event_item_timestamp(code_item)
        if ts is not None:
            goto_action = menu.addAction("Vai al tempo evento")
            goto_action.triggered.connect(
                lambda: self._seek_video_to_timestamp(float(ts))
            )

        event_id = code_item.data(Qt.ItemDataRole.UserRole)
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
                lambda: self._insert_code_before_event(code_item)
            )

        menu.exec(self.events_list.viewport().mapToGlobal(pos))

    def _apply_history_filter(self, _value=None):
        self.events_list.setRowCount(0)
        target_row = -1
        visible_rows = []
        for i, record in enumerate(self.history_records):
            kind = self._normalize_history_kind(record.get("kind"))
            if record.get("record_type") == "group":
                visible_rows.append(i)
                continue
            if not self._matches_history_filter(kind):
                continue
            visible_rows.append(i)

        self.events_list.setRowCount(len(visible_rows))
        for row_idx, rec_idx in enumerate(visible_rows):
            record = self.history_records[rec_idx]
            text = record.get("text", "")
            event_id = record.get("event_id")
            timestamp = self._history_timestamp_from_record(record)
            is_group = record.get("record_type") == "group"

            if is_group:
                group_item = QTableWidgetItem(text)
                group_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                fnt = QFont("Monospace", 8, QFont.Weight.Bold)
                fnt.setStyleHint(QFont.StyleHint.Monospace)
                group_item.setFont(fnt)
                bg = QColor("#78350F")
                group_item.setBackground(bg)
                group_item.setForeground(QColor("#FEF3C7"))
                self.events_list.setSpan(row_idx, 0, 1, 7)
                self.events_list.setItem(row_idx, 0, group_item)
                continue

            parts = self._parse_history_text(text)

            # Use structured record fields when available, fall back to parsed text
            score_str = parts["score"]
            sh = record.get("score_home")
            sa = record.get("score_away")
            if not score_str and sh is not None and sa is not None:
                score_str = f"{sh}-{sa}"

            set_str = parts["set_score"]
            sn = record.get("set_number")
            if not set_str and sn is not None:
                set_str = str(sn)

            ts_str = parts["system_time"]
            sdt = record.get("system_dt")
            if not ts_str and sdt:
                ts_str = sdt

            code_item = QTableWidgetItem(parts["code"])
            code_item.setData(Qt.ItemDataRole.UserRole, event_id)
            code_item.setToolTip(text)
            flags_item = QTableWidgetItem(parts["flags"])
            action_item = QTableWidgetItem(parts["action"])
            score_item = QTableWidgetItem(score_str)
            set_item = QTableWidgetItem(set_str)
            time_item = QTableWidgetItem(parts["match_time"])
            ts_item = QTableWidgetItem(ts_str)

            if event_id is not None:
                code_item.setData(Qt.ItemDataRole.UserRole, event_id)
            if timestamp is not None:
                code_item.setData(self.history_timestamp_role, float(timestamp))

            for col, item in enumerate([
                code_item, flags_item, action_item,
                score_item, set_item, time_item, ts_item
            ]):
                fnt = QFont("Monospace", 8)
                fnt.setStyleHint(QFont.StyleHint.Monospace)
                item.setFont(fnt)
                if col in (4, 5, 6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.events_list.setItem(row_idx, col, item)

            if (
                self._history_target_index is not None
                and rec_idx == self._history_target_index
            ):
                target_row = row_idx

        if target_row >= 0:
            self.events_list.scrollToItem(
                self.events_list.item(target_row, 0),
                QAbstractItemView.ScrollHint.PositionAtCenter,
            )
        else:
            self.events_list.scrollToBottom()
        self._highlight_history_by_current_time(scroll_to_active=False)

    def _parse_history_text(self, text: str) -> dict:
        result = {
            "code": text,
            "flags": "",
            "action": "",
            "score": "",
            "set_score": "",
            "match_time": "",
            "system_time": "",
        }
        if not text:
            return result
        try:
            ts_match = __import__("re").match(r"^(\d{2}:\d{2})\s*\|", text)
            if ts_match:
                result["match_time"] = ts_match.group(1)
            parts = text.split(" | ")
            if len(parts) >= 3:
                result["code"] = parts[-1].split(" -> ")[0].strip()
                if " -> " in parts[-1]:
                    score_part = parts[-1].split(" -> ")[1]
                    result["score"] = score_part.replace("-", "-")
            elif len(parts) == 2:
                result["code"] = parts[1]
            elif len(parts) == 1:
                result["code"] = parts[0]
            result["flags"] = ""
            result["action"] = parts[1] if len(parts) >= 2 else ""
        except Exception:
            pass
        return result

    def _append_history(
        self,
        text: str,
        event_id: int | None = None,
        kind: str = "SY",
        timestamp_seconds: float | None = None,
        insert_before_event_id: int | None = None,
        score_home: int | None = None,
        score_away: int | None = None,
        set_number: int | None = None,
        system_dt: str | None = None,
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

        if set_number is None:
            try:
                set_number = int(self.current_context.get("set_number", 0) or 0)
            except Exception:
                set_number = 0
        if score_home is None:
            try:
                score_home = int(self.current_context.get("score_home", 0) or 0)
            except Exception:
                score_home = None
        if score_away is None:
            try:
                score_away = int(self.current_context.get("score_away", 0) or 0)
            except Exception:
                score_away = None
        if system_dt is None:
            from datetime import datetime
            try:
                system_dt = datetime.now().strftime("%H:%M:%S")
            except Exception:
                system_dt = None

        record = {
            "text": final_text,
            "event_id": event_id,
            "kind": normalized_kind,
            "timestamp_seconds": ts,
            "score_home": score_home,
            "score_away": score_away,
            "set_number": set_number,
            "system_dt": system_dt,
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

    def _add_group_separator(self, label: str, timestamp_seconds: float | None = None):
        text = f"  {label}"
        ts = timestamp_seconds
        if ts is None:
            try:
                ts = self._event_video_timestamp()
            except Exception:
                ts = None
        if ts is not None:
            try:
                from datetime import datetime
                dt = datetime.fromtimestamp(float(ts))
                text = f"  {label}  —  {dt.strftime('%H:%M:%S')}"
            except Exception:
                pass
        record = {
            "text": text,
            "event_id": None,
            "kind": "GR",
            "timestamp_seconds": ts,
            "record_type": "group",
        }
        self.history_records.append(record)
        self._apply_history_filter()

    def _remove_history_item_by_event_id(self, event_id: int | None):
        # Rimuove un item dalla cronologia per ID
        if event_id is None:
            return

        self.history_records = [
            record
            for record in self.history_records
            if record.get("event_id") != event_id
        ]
        self._apply_history_filter()

    def _refresh_view(self):
        # Aggiorna tutta la vista dello scouting
        logger.debug("_refresh_view serving_side=%s serve_mode=%s reception_active=%s",
                      self.serving_side, self._serve_mode_active, self._reception_active)
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
            replaced_player=self._libero_active_player.get("home"),
            serving=self.serving_side == "home",
            setter_number=self.setter_number_by_side.get("home"),
        )
        self.away_court.update_lineup(
            away.get("name", "Trasferta"),
            away.get("lineup", {}),
            libero=away.get("libero"),
            replaced_player=self._libero_active_player.get("away"),
            serving=self.serving_side == "away",
            setter_number=self.setter_number_by_side.get("away"),
        )

        self._update_initial_service_controls()
        self._refresh_setter_numbers()
        self._update_outer_service_hints()
        self._update_reception_formation_display()
        self._update_set_scores_display()
        self._update_set_nav_buttons()
        self._sync_formation_view()

    def _update_set_scores_display(self):
        match_id = self.current_context.get("match_id") if self.current_context else None
        if not match_id or not self.db:
            self.set_scores_label.setVisible(False)
            return
        try:
            from volleyball_scout.core.models import MatchSet
            with self.db.session_scope() as session:
                sets = (
                    session.query(MatchSet)
                    .filter(MatchSet.match_id == match_id)
                    .order_by(MatchSet.set_number)
                    .all()
                )
            parts = []
            for s in sets:
                sh = int(s.score_home or 0)
                sa = int(s.score_away or 0)
                if sh > 0 or sa > 0:
                    parts.append(f"S{s.set_number}: {sh}-{sa}")
            if parts:
                self.set_scores_label.setText(" | ".join(parts))
                self.set_scores_label.setVisible(True)
            else:
                self.set_scores_label.setVisible(False)
        except Exception:
            self.set_scores_label.setVisible(False)

    def _update_set_nav_buttons(self):
        current = int(self.current_context.get("set_number", 1))
        print(f"[DEBUG] _update_set_nav_buttons: current={current}")
        self.btn_prev_set.setEnabled(current > 1)
        self.btn_next_set.setEnabled(current < 5)
        self.set_info.setText(f"Set {current}")

    def _switch_to_set(self, set_number: int):
        set_number = max(1, min(5, int(set_number)))
        current = int(self.current_context.get("set_number", 1))
        print(f"[DEBUG] _switch_to_set: {current} -> {set_number}")
        if set_number == current:
            return
        self.current_context["set_number"] = set_number
        self.current_set_id = None
        self._load_set_state_from_db(allow_redirect=False)
        print(f"[DEBUG] _switch_to_set: dopo load, set_number={self.current_context.get('set_number')}")
        self._populate_court_from_lineup()
        self._refresh_view()
        self._clear_player_highlight()
        self.serve_overlay.clear_trajectory()
        self.subtitle.setText(f"Set {set_number} caricato")
        self._add_group_separator(f"▶ Set {set_number}")

    def _go_to_prev_set(self):
        current = int(self.current_context.get("set_number", 1))
        self._switch_to_set(current - 1)

    def _go_to_next_set(self):
        current = int(self.current_context.get("set_number", 1))
        self._switch_to_set(current + 1)

    def _register_skill_event(self, skill_name: str):
        # Registra un evento skill rapido
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
        # Registra un timeout per la squadra
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

    def _on_libero_dropped(self, side: str, pos_code: str, player_number: str, libero_number: str):
        """Swap a player with the libero via drag-and-drop."""
        if not self.current_context:
            return
        team_key = "home_team" if side == "home" else "away_team"
        team_data = self.current_context.get(team_key, {})
        lineup = team_data.get("lineup", {})
        pos_code = str(pos_code)
        if pos_code not in lineup:
            return
        old_player = normalize_lineup_number(lineup.get(pos_code))
        if old_player is None:
            return
        old_player_str = str(old_player)
        if old_player_str == libero_number:
            return

        team_name = team_data.get("name", "Casa" if side == "home" else "Ospiti")

        lineup[pos_code] = libero_number
        self._libero_active_player[side] = old_player_str

        note = f"Libero {team_name}: #{old_player_str} ↔ #{libero_number}"
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
        self._save_lineups_to_db()
        self._refresh_view()

    def _on_libero_revert_requested(self, replaced_player: str):
        """Revert libero substitution: put the replaced player back in."""
        if not self.current_context:
            return
        side = self._find_side_for_replaced_player(replaced_player)
        if side is None:
            return
        team_key = "home_team" if side == "home" else "away_team"
        team_data = self.current_context.get(team_key, {})
        lineup = team_data.get("lineup", {})

        # Find the position currently occupied by the libero
        libero_num = normalize_lineup_number(team_data.get("libero"))
        if libero_num is None:
            return
        libero_pos = None
        for pos_code, num in lineup.items():
            if normalize_lineup_number(num) == libero_num:
                libero_pos = pos_code
                break
        if libero_pos is None:
            return

        # Put the replaced player back in that position
        lineup[libero_pos] = replaced_player
        self._libero_active_player[side] = None

        team_name = team_data.get("name", "Casa" if side == "home" else "Ospiti")
        note = f"Libero {team_name}: rientro #{replaced_player}"
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
        self._save_lineups_to_db()
        self._refresh_view()

    def _find_side_for_replaced_player(self, replaced_player: str) -> str | None:
        # Trova il lato per un giocatore sostituito dal libero
        for side in ("home", "away"):
            if self._libero_active_player.get(side) == replaced_player:
                return side
        return None

    def _register_substitution(self, side: str):
        # Registra una sostituzione
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
        # Registra un punto per la squadra
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
        self._save_set_scores()

        self._append_history(
            f"{self._format_elapsed()} | Punto {point_result['team_name']} -> {point_result['score_home']}-{point_result['score_away']}",
            event_id=event_id,
            kind=self.HISTORY_KIND_POINT,
        )

        self._refresh_view()

    def _undo_last_rally(self):
        # Annulla l'ultimo rally
        if not self.rally_history:
            return

        action = self.rally_history.pop()
        self._restore_state(action["snapshot"])

        event_id = action.get("event_id")
        self._delete_event(event_id)
        self._remove_history_item_by_event_id(event_id)

        self.subtitle.setText("Ultimo rally annullato.")

    def _on_serving_selected(self, side: str):
        # Gestisce la selezione della squadra al servizio
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
        # Determina il percorso video per il match
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
        # Salva il link video alla chiusura del match
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

        score_text = f"{score_home}-{score_away}"
        self._add_group_separator(f"Fine Set {set_number}  ({score_text})")

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

        skill = getattr(event, "skill", None)
        if skill and str(skill).strip():
            return self.HISTORY_KIND_SKILL

        note = (getattr(event, "notes", "") or "").strip().lower()
        if note.startswith("punto"):
            return self.HISTORY_KIND_POINT
        if note.startswith("evento rapido"):
            return self.HISTORY_KIND_SKILL
        return self.HISTORY_KIND_SYSTEM

    def _load_set_state_from_db(self, allow_redirect=True):
        """Carica punteggio/eventi già salvati del set corrente."""
        self.current_set_id = None
        self.event_counter = 0
        self.history_records = []
        self.active_history_event_id = None
        self.events_list.setRowCount(0)

        if self.db is None or not self.current_context:
            return

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchSet, ScoutEvent

                set_record = self._ensure_set_record(session)
                if set_record is not None:
                    self.current_context["score_home"] = 0
                    self.current_context["score_away"] = 0
                    self.elapsed_seconds = int(set_record.duration or 0)
                    self.elapsed_seconds_exact = float(max(0, self.elapsed_seconds))

                    match_id = self.current_context.get("match_id")

                    events = (
                        session.query(ScoutEvent)
                        .filter(ScoutEvent.match_id == match_id)
                        .order_by(ScoutEvent.id.asc())
                        .all()
                    )

                    current_set_num = int(self.current_context.get("set_number", 1) or 1)
                    self._history_target_index = None
                    for event in events:
                        set_n = event.match_set.set_number if event.match_set else 1
                        note = event.notes or "Evento scouting"
                        rot = getattr(event, "rotation", None)
                        rot_str = f" [R{rot}]" if rot and rot > 0 else ""
                        timestamp_text = self._format_seconds(
                            int(getattr(event, "video_timestamp", 0) or 0)
                        )
                        event_timestamp = float(
                            max(
                                0.0,
                                float(getattr(event, "video_timestamp", 0.0) or 0.0),
                            )
                        )
                        sh = getattr(event, "score_home", None)
                        sa_attr = getattr(event, "score_away", None)
                        created = getattr(event, "created_at", None)
                        system_dt_str = created.strftime("%H:%M:%S") if created else None
                        self.history_records.append(
                            {
                                "text": f"[S{set_n}] {timestamp_text}{rot_str} | {note}",
                                "event_id": event.id,
                                "kind": self._history_kind_from_event(event),
                                "timestamp_seconds": event_timestamp,
                                "score_home": sh,
                                "score_away": sa_attr,
                                "set_number": set_n,
                                "system_dt": system_dt_str,
                            }
                        )
                        if event.rally_number is not None:
                            self.event_counter = max(
                                self.event_counter, int(event.rally_number)
                            )
                        if set_n == current_set_num and self._history_target_index is None:
                            self._history_target_index = len(self.history_records) - 1

            self._apply_history_filter()

        except Exception as e:
            print(f"⚠️ Errore caricamento stato set: {e}")

    def load_match_context(self, context: dict):
        """Carica match e formazioni nella vista scouting live."""
        self._migrate_schema()
        self._formations_by_rotation = {"home": {}, "away": {}}
        if not context:
            self.point_outcome_map = self._load_point_outcome_map("global")
            self.events_list.setRowCount(0)
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
            self._formation_view.update_lineups({}, {})
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

        if self._serve_mode_active:
            self._exit_serve_mode()
        if self._attack_mode_active:
            self._exit_attack_mode()
        self.current_context = deepcopy(context)
        self.current_context.setdefault("score_home", 0)
        self.current_context.setdefault("score_away", 0)
        self.current_context.setdefault("set_number", 1)
        print(f"[DEBUG] load_match_context: set_number iniziale = {self.current_context.get('set_number')}")
        print(f"[DEBUG] load_match_context: match_id = {self.current_context.get('match_id')}")
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
            settings = self._shortcuts_settings()
            home_manual = self.formation_manager.load_reception_positions(
                "home",
                self.current_context.get("match_id"),
                self.current_context.get("set_number"),
                settings,
                self.RECEPTION_MEMORY_SETTINGS_PREFIX,
            )
        if not away_manual:
            if not home_manual:
                settings = self._shortcuts_settings()
            away_manual = self.formation_manager.load_reception_positions(
                "away",
                self.current_context.get("match_id"),
                self.current_context.get("set_number"),
                settings,
                self.RECEPTION_MEMORY_SETTINGS_PREFIX,
            )

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

        # Se il set corrente non ha eventi, passa al primo set con dati
        self._ensure_set_with_events()

        self._load_set_state_from_db()

        self._populate_court_from_lineup()

        n_events = len(self.history_records)
        logger.info("load_match_context: n_eventi caricati=%d", n_events)
        if hasattr(self, "subtitle"):
            if n_events > 0:
                self.subtitle.setText(f"{n_events} eventi caricati dal DB. Pronto.")
            else:
                self.subtitle.setText("Nessun evento trovato. Inizia lo scouting.")

        if self.history_records:
            first_ts = self.history_records[0].get("timestamp_seconds", 0)
            self.elapsed_seconds = int(first_ts)
            self.elapsed_seconds_exact = float(first_ts)
        elif self._resume_video_seconds is not None:
            self.elapsed_seconds_exact = float(max(0.0, self._resume_video_seconds))
            self.elapsed_seconds = int(self.elapsed_seconds_exact)
        else:
            self.elapsed_seconds_exact = float(max(0, int(self.elapsed_seconds or 0)))
        self._refresh_setter_numbers()
        self._formations_by_rotation = {
            "home": self.formation_manager.load_formations(
                "home",
                self.current_context.get("match_id"),
                self.current_context.get("set_number"),
            ),
            "away": self.formation_manager.load_formations(
                "away",
                self.current_context.get("match_id"),
                self.current_context.get("set_number"),
            ),
        }
        logger.debug("formations loaded: home=%s away=%s",
                      sorted(self._formations_by_rotation["home"].keys()) if self._formations_by_rotation["home"] else "{}",
                      sorted(self._formations_by_rotation["away"].keys()) if self._formations_by_rotation["away"] else "{}")

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
            msg = "Formazioni set caricate. Pronto per scoutizzare."
            if n_events:
                msg = f"{n_events} eventi caricati. {msg}"
            self.subtitle.setText(msg)
        else:
            self.subtitle.setText(
                "Seleziona la battuta iniziale per iniziare lo scouting."
            )
        self.match_info.setText(
            f"Partita #{match_id}: {home.get('name', 'Casa')} vs {away.get('name', 'Trasferta')}"
        )
        self.set_info.setText(f"Set {self.current_context.get('set_number', 1)}")

        if not self.history_records:
            set_num = self.current_context.get("set_number", 1)
            self._add_group_separator(f"Inizio Set {set_num}")

        self._refresh_view()
        self._set_controls_enabled(True)
        self._update_video_pause_controls()

        self._highlight_history_by_current_time(scroll_to_active=False)
        self.setFocus()

    def _migrate_schema(self):
        try:
            if self.db:
                from sqlalchemy import text as sa_text
                with self.db.session_scope() as session:
                    session.execute(sa_text("ALTER TABLE scout_events ADD COLUMN rotation INTEGER DEFAULT 1"))
        except Exception:
            pass
        try:
            if self.db:
                from sqlalchemy import text as sa_text
                with self.db.session_scope() as session:
                    session.execute(sa_text("ALTER TABLE match_sets ADD COLUMN home_lineup TEXT DEFAULT NULL"))
        except Exception:
            pass
        try:
            if self.db:
                from sqlalchemy import text as sa_text
                with self.db.session_scope() as session:
                    session.execute(sa_text("ALTER TABLE match_sets ADD COLUMN away_lineup TEXT DEFAULT NULL"))
        except Exception:
            pass

    def closeEvent(self, event):
        """Gestisce la chiusura del pannello di scouting."""
        if self.timer_running:
            self.timer.stop()
            self.timer_running = False

        if self.video_detached_window is not None:
            self._is_docking_video = True
            try:
                self.video_detached_window.hide()
                self.video_detached_window.deleteLater()
            finally:
                self._is_docking_video = False
            self.video_detached_window = None

        super().closeEvent(event)

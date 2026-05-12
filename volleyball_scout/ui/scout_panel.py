import re
from copy import deepcopy

from PyQt6.QtCore import QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
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

    serving_requested = pyqtSignal(str)
    VISUAL_GRID = (("P4", "P3", "P2"), ("P5", "P6", "P1"))

    def __init__(self, team_side: str, team_name="Squadra", parent=None):
        super().__init__(parent)
        self.team_side = team_side
        self._number_labels = {}
        self._serving_badge = QPushButton()
        self._libero_label = QLabel()
        self._highlight_number = None
        self._setup_ui(team_name)

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
                background-color: #3A2D27;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self._serving_badge = QPushButton("RICEZIONE")
        self._serving_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self._serving_badge.setToolTip(
            "Clicca per impostare questa squadra al servizio (battuta)"
        )
        self._serving_badge.clicked.connect(
            lambda: self.serving_requested.emit(self.team_side)
        )
        layout.addWidget(self._serving_badge)

        grid = QGridLayout()
        grid.setSpacing(8)

        for row, row_positions in enumerate(self.VISUAL_GRID):
            for col, pos_code in enumerate(row_positions):
                cell = QFrame()
                cell.setMinimumSize(76, 70)
                cell.setStyleSheet(
                    """
                    QFrame {
                        border: 1px solid #E2B37A;
                        border-radius: 8px;
                        background-color: #DDAA5B;
                    }
                    """
                )
                cell_layout = QVBoxLayout(cell)
                cell_layout.setContentsMargins(4, 4, 4, 4)
                cell_layout.setSpacing(0)

                number_label = QLabel("-")
                number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                number_label.setStyleSheet(
                    "font-size: 24px; font-weight: bold; color: #2B211C;"
                )

                pos_label = QLabel(pos_code)
                pos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pos_label.setStyleSheet("font-size: 10px; color: #2B211C;")

                cell_layout.addWidget(number_label, 1)
                cell_layout.addWidget(pos_label)

                self._number_labels[pos_code] = number_label
                grid.addWidget(cell, row, col)

        layout.addLayout(grid)

        self._libero_label = QLabel("Libero: -")
        self._libero_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._libero_label.setStyleSheet(
            "font-size: 11px; color: #EED9C4; padding: 2px 0;"
        )
        layout.addWidget(self._libero_label)

    def _normalize_player_number(self, value) -> str | None:
        if value is None:
            return None
        raw = str(value).strip()
        if not raw or raw == "-":
            return None
        try:
            return str(int(raw))
        except Exception:
            return raw.lstrip("0") or raw

    def _apply_number_style(self, label: QLabel, highlighted: bool):
        if highlighted:
            label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #F8FAFC; background-color: #DC2626; border-radius: 8px;"
            )
        else:
            label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2B211C;")

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
        self, team_name: str, positions: dict, libero=None, serving=False
    ):
        self.setTitle(team_name or "Squadra")

        for pos_code, label in self._number_labels.items():
            value = positions.get(pos_code) if positions else None
            label.setText(str(value) if value is not None else "-")
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
                QPushButton {
                    background-color: #E95420;
                    color: white;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border: 1px solid #C2410C;
                }
                QPushButton:hover { background-color: #F06A3A; }
                """
            )
        else:
            self._serving_badge.setText("RICEZIONE")
            self._serving_badge.setStyleSheet(
                """
                QPushButton {
                    background-color: #4B5563;
                    color: #F6EFE9;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    border: 1px solid #374151;
                }
                QPushButton:hover { background-color: #6B7280; }
                """
            )


class ScoutPanel(QWidget):
    """Schermata Scouting Live con doppio campo allineato."""

    set_finished = pyqtSignal(dict)

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
    SHORTCUTS_SETTINGS_ORG = "VolleyballScout"
    SHORTCUTS_SETTINGS_APP = "ScoutPanel"
    SHORTCUTS_SETTINGS_KEY = "code_shortcuts"

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
        self.timer_running = False
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_timer_tick)

        self.skill_buttons = []
        self.code_shortcut_buttons = []
        self.code_keypad_buttons = []
        self.code_shortcuts = self._load_shortcuts_config()
        self.history_records = []
        self.timeouts_used = {"home": 0, "away": 0}

        # Sync video -> timestamp evento
        self.video_source_info = {}
        self.video_timestamp_seconds = None

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

        timer_layout.addStretch()
        timer_layout.addWidget(self.timer_label)
        timer_layout.addWidget(self.btn_timer_toggle)
        timer_layout.addWidget(self.btn_timer_reset)
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
        score_buttons_layout.addStretch()
        layout.addLayout(score_buttons_layout)

        hint = QLabel(
            "Tip: clicca BATTUTA/RICEZIONE su un campo per impostare manualmente la squadra al servizio"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-size: 10px; color: #D9CFC5;")
        layout.addWidget(hint)

        courts_row = QHBoxLayout()
        courts_row.setSpacing(12)

        self.home_court = TeamCourtWidget("home", "Casa")
        self.away_court = TeamCourtWidget("away", "Trasferta")
        self.home_court.serving_requested.connect(self._on_serving_selected)
        self.away_court.serving_requested.connect(self._on_serving_selected)

        center_line = QFrame()
        center_line.setFixedWidth(3)
        center_line.setStyleSheet("background-color: #111827; border-radius: 1px;")

        courts_row.addWidget(self.home_court, 1)
        courts_row.addWidget(center_line)
        courts_row.addWidget(self.away_court, 1)
        layout.addLayout(courts_row, 1)

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

        self.btn_config_shortcuts = QPushButton("Configura tasti")
        self.btn_config_shortcuts.clicked.connect(self._configure_code_shortcuts)
        shortcuts_header_row.addWidget(self.btn_config_shortcuts)

        self.btn_reset_shortcuts = QPushButton("Reset")
        self.btn_reset_shortcuts.clicked.connect(self._reset_code_shortcuts)
        shortcuts_header_row.addWidget(self.btn_reset_shortcuts)

        shortcuts_header_row.addStretch()
        datavolley_layout.addLayout(shortcuts_header_row)

        self.shortcuts_buttons_widget = QWidget()
        self.shortcuts_layout = QGridLayout(self.shortcuts_buttons_widget)
        self.shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        self.shortcuts_layout.setSpacing(6)
        datavolley_layout.addWidget(self.shortcuts_buttons_widget)

        self._rebuild_code_shortcut_buttons()
        self._create_datavolley_keypad(datavolley_layout)

        layout.addWidget(datavolley_group)

        skills_group = QGroupBox("Eventi rapidi")
        skills_layout = QGridLayout(skills_group)
        skills_layout.setSpacing(8)

        skills = [
            ("Attacco", QStyle.StandardPixmap.SP_MediaPlay),
            ("Muro", QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("Battuta", QStyle.StandardPixmap.SP_BrowserReload),
            ("Ricezione", QStyle.StandardPixmap.SP_DialogOpenButton),
            ("Alzata", QStyle.StandardPixmap.SP_ArrowForward),
            ("Difesa", QStyle.StandardPixmap.SP_ArrowBack),
        ]

        for idx, (label, icon_type) in enumerate(skills):
            btn = QPushButton(label)
            btn.setMinimumHeight(42)
            btn.setIcon(self.style().standardIcon(icon_type))
            btn.clicked.connect(lambda _, n=label: self._register_skill_event(n))
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #8A613F;
                    color: white;
                    border: 1px solid #6E4B32;
                    border-radius: 6px;
                    font-weight: bold;
                    text-align: left;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #A5784D;
                }
                QPushButton:pressed {
                    background-color: #6E4B32;
                }
                """
            )
            self.skill_buttons.append(btn)
            skills_layout.addWidget(btn, idx // 2, idx % 2)

        layout.addWidget(skills_group)

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
        history_layout.addWidget(self.events_list)

        history_side_layout.addWidget(self.codes_group, 1)
        root_layout.addWidget(history_panel, 2)

    def _toggle_codes_panel(self, is_visible: bool):
        self.codes_group.setVisible(is_visible)
        self.btn_toggle_codes.setText(
            "Nascondi elenco codici" if is_visible else "Mostra elenco codici"
        )

    def _shortcuts_settings(self) -> QSettings:
        return QSettings(self.SHORTCUTS_SETTINGS_ORG, self.SHORTCUTS_SETTINGS_APP)

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
        min_h: int = 30,
        max_w: int | None = None,
    ) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(min_h)
        if max_w is not None:
            btn.setMaximumWidth(max_w)
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

    def _create_datavolley_keypad(self, parent_layout: QVBoxLayout):
        keypad_group = QGroupBox("Tastierino DataVolley")
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

        parent_layout.addWidget(keypad_group)

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

        key = event.key()
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

    def set_video_source(self, source_info: dict | None):
        """Riceve info sorgente video dal player (file/webcam/ip)."""
        self.video_source_info = dict(source_info or {})

    def set_video_time(self, seconds: float | None):
        """Aggiorna il timestamp video corrente usato per gli eventi."""
        try:
            self.video_timestamp_seconds = (
                None if seconds is None else max(0.0, float(seconds))
            )
        except Exception:
            self.video_timestamp_seconds = None

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
        self, side: str, evaluation: str | None
    ) -> str | None:
        if evaluation == "#":
            return side
        if evaluation == "=":
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

        evaluation = parsed.get("evaluation")
        point_side = self._resolve_point_team_from_evaluation(side, evaluation)

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
            skill=parsed.get("skill"),
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

        self.code_input.clear()
        self.code_input.setFocus()

    def _set_controls_enabled(self, enabled: bool):
        self.btn_point_home.setEnabled(enabled)
        self.btn_point_away.setEnabled(enabled)
        self.btn_undo.setEnabled(enabled)
        self.btn_finish_set.setEnabled(enabled)
        self.btn_finish_match.setEnabled(enabled)
        self.btn_set_actions.setEnabled(enabled)
        self.home_court.setEnabled(enabled)
        self.away_court.setEnabled(enabled)
        self.btn_timer_toggle.setEnabled(enabled)
        self.btn_timer_reset.setEnabled(enabled)

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
        return self._format_seconds(self.elapsed_seconds)

    def _reset_timer_ui(self):
        self.timer_label.setText(self._format_elapsed())
        self.btn_timer_toggle.setText("Avvia timer")

    def _on_timer_tick(self):
        self.elapsed_seconds += 1
        self.timer_label.setText(self._format_elapsed())

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
        self.elapsed_seconds = 0
        self.timer_label.setText(self._format_elapsed())

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

    def _rotate_team_lineup(self, side: str):
        """Rotazione oraria: P2→P1, P3→P2, ..., P1→P6."""
        team_key = "home_team" if side == "home" else "away_team"
        team_data = self.current_context.get(team_key, {})
        lineup = dict(team_data.get("lineup", {}))

        old_p1 = lineup.get("P1")
        old_p2 = lineup.get("P2")
        old_p3 = lineup.get("P3")
        old_p4 = lineup.get("P4")
        old_p5 = lineup.get("P5")
        old_p6 = lineup.get("P6")

        lineup["P1"] = old_p2
        lineup["P2"] = old_p3
        lineup["P3"] = old_p4
        lineup["P4"] = old_p5
        lineup["P5"] = old_p6
        lineup["P6"] = old_p1

        team_data["lineup"] = lineup

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
                    video_timestamp=self._event_video_timestamp(),
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
            self.events_list.addItem(item)

        self.events_list.scrollToBottom()

    def _append_history(
        self,
        text: str,
        event_id: int | None = None,
        kind: str = "SY",
    ):
        self.history_records.append(
            {
                "text": text,
                "event_id": event_id,
                "kind": self._normalize_history_kind(kind),
            }
        )
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
        )
        self.away_court.update_lineup(
            away.get("name", "Trasferta"),
            away.get("lineup", {}),
            libero=away.get("libero"),
            serving=self.serving_side == "away",
        )

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

        self._apply_serving_side(side)
        self.subtitle.setText("Servizio impostato manualmente.")

        team_name = (
            self.current_context.get("home_team", {}).get("name", "Casa")
            if side == "home"
            else self.current_context.get("away_team", {}).get("name", "Ospiti")
        )

        event_id = self._persist_event(
            team_side=side,
            skill="S",
            notes="Cambio servizio manuale",
            kind=self.HISTORY_KIND_SYSTEM,
        )
        self._append_history(
            f"{self._format_elapsed()} | Cambio servizio manuale: {team_name}",
            event_id=event_id,
            kind=self.HISTORY_KIND_SYSTEM,
        )

        self._refresh_view()

    def _compute_sets_won(self, session, match_id: int) -> tuple[int, int]:
        """Conta i set vinti per home/away per il match."""
        from volleyball_scout.core.models import MatchSet

        all_sets = session.query(MatchSet).filter_by(match_id=match_id).all()
        home_sets_won = sum(1 for s in all_sets if s.winner == "home")
        away_sets_won = sum(1 for s in all_sets if s.winner == "away")
        return home_sets_won, away_sets_won

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
                        set_record.duration = int(self.elapsed_seconds)
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
                "duration_seconds": int(self.elapsed_seconds),
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

        home_sets_won = 0
        away_sets_won = 0
        match_winner = None

        if self.db is not None and match_id is not None:
            try:
                with self.db.session_scope() as session:
                    from volleyball_scout.core.models import Match

                    set_record = self._ensure_set_record(session)
                    if set_record is not None:
                        set_record.score_home = score_home
                        set_record.score_away = score_away
                        set_record.duration = int(self.elapsed_seconds)
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
                "duration_seconds": int(self.elapsed_seconds),
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
                        self.history_records.append(
                            {
                                "text": f"{timestamp_text} | {note}",
                                "event_id": event.id,
                                "kind": self._history_kind_from_event(event),
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
            self.timeouts_used = {"home": 0, "away": 0}
            self.video_timestamp_seconds = None
            self.events_list.clear()
            if self.timer_running:
                self._toggle_timer()
            self.elapsed_seconds = 0
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

        self.rally_history.clear()
        self.timeouts_used = {"home": 0, "away": 0}
        self.video_timestamp_seconds = None
        self.serving_side = self._resolve_serving_side(self.current_context)
        self._apply_serving_side(self.serving_side)
        if hasattr(self, "code_input"):
            self.code_input.clear()
        self._clear_player_highlight()

        self._load_set_state_from_db()

        home = self.current_context.get("home_team", {})
        away = self.current_context.get("away_team", {})
        match_id = self.current_context.get("match_id", "-")

        self.subtitle.setText("Formazioni set caricate. Pronto per scoutizzare.")
        self.match_info.setText(
            f"Partita #{match_id}: {home.get('name', 'Casa')} vs {away.get('name', 'Trasferta')}"
        )
        self.set_info.setText(f"Set {self.current_context.get('set_number', 1)}")

        self._refresh_view()
        self._set_controls_enabled(True)

        if self.timer_running:
            self._toggle_timer()
        self._toggle_timer()
        self.setFocus()

    def closeEvent(self, event):
        if self.timer_running:
            self.timer.stop()
            self.timer_running = False
        super().closeEvent(event)

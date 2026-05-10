"""
Volleyball Scout - Roster Setup Widget
Gestisce l'assegnazione dei giocatori a una partita
Con sistema di frecce per trasferimento giocatori tra disponibili e roster
"""

import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Ensure imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Match, MatchPlayer, Player

try:
    from volleyball_scout.ui.assets import get_role_icon
except Exception:
    get_role_icon = None


class RosterSetupWidget(QWidget):
    """Widget per configurare la Gestione Squadre di una partita con sistema frecce"""

    MAX_PLAYERS_PER_TEAM = 14

    # Signal emesso quando il roster setup è completato
    roster_completed = pyqtSignal()

    def __init__(
        self, db_manager: DatabaseManager, match_id: int | None = None, parent=None
    ):
        """
        Inizializza il RosterSetupWidget.

        Args:
            db_manager: DatabaseManager istanza
            match_id: Se presente, modalità "Setup per Partita"
                     Se None, modalità "Setup Generale" (seleziona partita manualmente)
            parent: Parent widget
        """
        super().__init__(parent)
        self.db = db_manager
        self.match_id = match_id
        self.current_match = None
        self.current_team_id = None
        self.current_team_index = 0
        self.teams = []
        # Stato roster corrente (solo team attivo)
        # {player_id: {"number": int, "role": str, "team_id": int}}
        self.selected_players = {}
        # Stato roster per team
        # {team_id: {player_id: {"number": int, "role": str, "team_id": int}}}
        self.team_selected_players = {}
        # Snapshot iniziale per mostrare "Aggiunto" vs "Presente"
        # {team_id: set(player_id)}
        self.initial_team_players = {}
        # Log eventi aggiunta/rimozione per team
        # {team_id: [{"action": "added|removed", "player_id": int, "text": str}]}
        self.team_change_events = {}
        # Cache dei dati dei giocatori per evitare query ripetute
        self.players_cache = {}
        self._updating_roster_table = False

        self._setup_ui()

        # Se match_id è fornito, carica direttamente il match
        if self.match_id:
            self._load_match(self.match_id)

    def _setup_ui(self):
        """Crea l'interfaccia utente"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Titolo
        title = QLabel("Gestione Squadre")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        main_layout.addWidget(title)

        # Uso di QStackedWidget per due modalità
        self.stacked = QStackedWidget()

        # Index 0: Selezione partita (modalità generale)
        self._setup_match_selection_page()

        # Index 1: Setup roster per partita (con frecce)
        self._setup_roster_setup_page()

        self.stacked.addWidget(self.match_selection_widget)
        self.stacked.addWidget(self.roster_setup_widget)

        main_layout.addWidget(self.stacked)

        # Se match_id è fornito, vai direttamente alla pagina 1
        if self.match_id:
            self.stacked.setCurrentIndex(1)
        else:
            self.stacked.setCurrentIndex(0)

    def _setup_match_selection_page(self):
        """Crea la pagina di selezione partita"""
        self.match_selection_widget = QWidget()
        layout = QVBoxLayout(self.match_selection_widget)

        layout.addWidget(QLabel("Seleziona una partita per configurare il roster"))

        # Matches list
        matches_section = QGroupBox("Partite Disponibili")
        matches_layout = QVBoxLayout()

        self.matches_list = QListWidget()
        self.matches_list.itemClicked.connect(self._on_match_selected)
        matches_layout.addWidget(self.matches_list)

        matches_section.setLayout(matches_layout)
        layout.addWidget(matches_section)

        layout.addStretch()

        self.load_matches()

    def _setup_roster_setup_page(self):
        """Crea la pagina di setup del roster con sistema di frecce"""
        self.roster_setup_widget = QWidget()
        layout = QVBoxLayout(self.roster_setup_widget)

        # Header con info partita
        header_layout = QHBoxLayout()
        self.label_match_info = QLabel()
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_match_info.setFont(font)
        header_layout.addWidget(self.label_match_info)
        header_layout.addStretch()

        if not self.match_id:
            btn_back = QPushButton("Indietro")
            btn_back.setMaximumWidth(120)
            btn_back.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
            )
            btn_back.clicked.connect(self._go_back_to_selection)
            header_layout.addWidget(btn_back)

        layout.addLayout(header_layout)

        # Sottotitolo team selector (senza menu a tendina)
        team_layout = QHBoxLayout()
        self.label_current_team = QLabel("Squadra corrente: -")
        self.label_current_team.setStyleSheet("font-weight: bold;")
        team_layout.addWidget(self.label_current_team)

        # Manteniamo il combo nascosto solo per gestione indice interna
        self.combo_teams = QComboBox()
        self.combo_teams.currentIndexChanged.connect(self._on_team_changed)
        self.combo_teams.setVisible(False)
        self.combo_teams.setEnabled(False)
        team_layout.addWidget(self.combo_teams)

        self.label_team_step = QLabel("Step roster: -")
        self.label_team_step.setStyleSheet("font-size: 11px;")
        team_layout.addWidget(self.label_team_step)

        team_layout.addStretch()
        layout.addLayout(team_layout)

        # Corpo principale: 20% | 20% | 60%
        body_layout = QHBoxLayout()
        body_layout.setSpacing(10)

        # ============ SINISTRA (20%): GIOCATORI DISPONIBILI ============
        left_widget = self._create_available_players_section()
        body_layout.addWidget(left_widget, 1)  # 20%

        # ============ CENTRO (20%): PULSANTI FRECCIA ============
        center_widget = self._create_arrow_buttons_section()
        body_layout.addWidget(center_widget, 1)  # 20%

        # ============ DESTRA (60%): ROSTER PARTITA ============
        right_widget = self._create_roster_table_section()
        body_layout.addWidget(right_widget, 3)  # 60%

        layout.addLayout(body_layout, 1)

        # Footer: Salva e Annulla
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_continue = QPushButton("Continua")
        self.btn_continue.setMinimumWidth(180)
        self.btn_continue.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
        )
        self.btn_continue.clicked.connect(self._save_roster)
        footer_layout.addWidget(self.btn_continue)

        if not self.match_id:
            btn_cancel = QPushButton("Annulla")
            btn_cancel.setMinimumWidth(150)
            btn_cancel.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
            )
            btn_cancel.clicked.connect(self._go_back_to_selection)
            footer_layout.addWidget(btn_cancel)

        layout.addLayout(footer_layout)

    def _create_available_players_section(self):
        """Crea la sezione sinistra: Giocatori Disponibili"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Titolo
        title = QLabel("<b>Giocatori Disponibili</b>")
        layout.addWidget(title)

        # Lista giocatori (QListWidget, cliccabili, no checkbox)
        self.list_available_players = QListWidget()
        self.list_available_players.setIconSize(QSize(18, 18))
        self.list_available_players.setStyleSheet("""
            QListWidget {
                border: 1px solid #B79C8A;
                border-radius: 8px;
            }
            QListWidget::item {
                padding-top: 5px;
                padding-bottom: 5px;
            }
            QListWidget::item:selected {
                background-color: #E95420;
                color: white;
            }
        """)
        self.list_available_players.itemSelectionChanged.connect(
            self._on_available_player_selected
        )
        self.list_available_players.itemDoubleClicked.connect(
            self._on_available_player_double_clicked
        )
        layout.addWidget(self.list_available_players)

        # Hint
        hint = QLabel("<i>Doppio-click per aggiungere</i>")
        hint.setStyleSheet("font-size: 10px;")
        layout.addWidget(hint)

        return widget

    def _create_arrow_buttons_section(self):
        """Crea la sezione centrale: Pulsanti Freccia"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Contatore giocatori caricati
        self.label_roster_counter = QLabel(
            f"Giocatori caricati: 0/{self.MAX_PLAYERS_PER_TEAM}"
        )
        self.label_roster_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_roster_counter.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #8A613F;"
        )
        layout.addWidget(self.label_roster_counter)
        layout.addSpacing(8)

        # Freccia singolo →
        self.btn_add_single = QPushButton("Singolo →")
        self.btn_add_single.setMinimumHeight(52)
        self.btn_add_single.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
        )
        self.btn_add_single.clicked.connect(lambda: self._on_add_single_player())
        self.btn_add_single.setStyleSheet(
            """
            QPushButton {
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                background-color: #E95420;
                color: white;
                border: 2px solid #C7451A;
            }
            QPushButton:hover {
                background-color: #F06B3C;
            }
            QPushButton:pressed {
                background-color: #C7451A;
            }
        """
        )
        layout.addWidget(self.btn_add_single)

        # Freccia tutti ⇒
        self.btn_add_all = QPushButton("Tutti ⇒")
        self.btn_add_all.setMinimumHeight(52)
        self.btn_add_all.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward)
        )
        self.btn_add_all.clicked.connect(lambda: self._on_add_all_players())
        self.btn_add_all.setStyleSheet(
            """
            QPushButton {
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                background-color: #E95420;
                color: white;
                border: 2px solid #C7451A;
            }
            QPushButton:hover {
                background-color: #F06B3C;
            }
            QPushButton:pressed {
                background-color: #C7451A;
            }
        """
        )
        layout.addWidget(self.btn_add_all)

        layout.addSpacing(20)

        # Freccia singolo ←
        self.btn_remove_single = QPushButton("Singolo ←")
        self.btn_remove_single.setMinimumHeight(52)
        self.btn_remove_single.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
        )
        self.btn_remove_single.clicked.connect(lambda: self._on_remove_single_player())
        self.btn_remove_single.setStyleSheet(
            """
            QPushButton {
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                background-color: #8A613F;
                color: white;
                border: 2px solid #6E4B32;
            }
            QPushButton:hover {
                background-color: #A5784D;
            }
            QPushButton:pressed {
                background-color: #6E4B32;
            }
        """
        )
        layout.addWidget(self.btn_remove_single)

        layout.addStretch()

        return widget

    def _create_roster_table_section(self):
        """Crea la sezione destra: Roster Partita"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Titolo
        title = QLabel("<b>Giocatori in partita</b>")
        title.setStyleSheet("font-size: 16px;")
        layout.addWidget(title)
        # Tabella con giocatori selezionati
        # Colonne: Nome, Cognome, Ruolo, Capitano, Azioni (delete)
        self.table_roster = QTableWidget()
        self.table_roster.setColumnCount(5)
        self.table_roster.setHorizontalHeaderLabels(
            ["Nome", "Cognome", "Ruolo", "Cap.", "Azioni"]
        )
        self.table_roster.verticalHeader().setVisible(False)  # nasconde numeri di riga
        self.table_roster.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #B79C8A;
                border-radius: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E95420;
                color: white;
            }
            QHeaderView::section {
                border: 1px solid #B79C8A;
                padding: 4px;
            }
            """
        )

        header = self.table_roster.horizontalHeader()
        try:
            # PyQt6
            stretch = QHeaderView.ResizeMode.Stretch
            resize_to_contents = QHeaderView.ResizeMode.ResizeToContents
        except AttributeError:
            # PyQt5
            stretch = QHeaderView.Stretch
            resize_to_contents = QHeaderView.ResizeToContents

        header.setSectionResizeMode(0, stretch)  # Nome
        header.setSectionResizeMode(1, stretch)  # Cognome
        header.setSectionResizeMode(2, resize_to_contents)  # Ruolo
        header.setSectionResizeMode(3, resize_to_contents)  # Cap.
        header.setSectionResizeMode(4, resize_to_contents)  # ❌

        self.table_roster.itemDoubleClicked.connect(self._on_roster_item_double_clicked)
        self.table_roster.itemChanged.connect(self._on_roster_table_item_changed)
        layout.addWidget(self.table_roster)

        # Log eventi di modifica roster per il team corrente
        events_title = QLabel("<b>Eventi roster (aggiunti/rimossi)</b>")
        events_title.setStyleSheet("font-size: 12px;")
        layout.addWidget(events_title)

        self.list_roster_events = QListWidget()
        self.list_roster_events.setMaximumHeight(130)
        self.list_roster_events.setStyleSheet(
            """
            QListWidget {
                font-size: 11px;
                border: 1px solid #B79C8A;
                border-radius: 8px;
            }
            """
        )
        layout.addWidget(self.list_roster_events)

        return widget

    def load_matches(self):
        """Carica le partite dal database (modalità selezione)"""
        self.matches_list.clear()

        try:
            with self.db.session_scope() as session:
                # Nuovo flusso: solo match ancora da iniziare
                matches = session.query(Match).filter(Match.status == "draft").all()

                if not matches:
                    item = QListWidgetItem("(Nessuna partita)")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    self.matches_list.addItem(item)
                else:
                    for match in matches:
                        home = match.home_team.name if match.home_team else "?"
                        away = match.away_team.name if match.away_team else "?"
                        date_str = (
                            match.date.strftime("%Y-%m-%d %H:%M") if match.date else "-"
                        )
                        display_text = f"{home} vs {away} ({date_str})"
                        item = QListWidgetItem(display_text)
                        item.setData(Qt.ItemDataRole.UserRole, match.id)
                        self.matches_list.addItem(item)

        except Exception as e:
            print(f"❌ Errore caricamento partite: {e}")

    def _on_match_selected(self, item: QListWidgetItem):
        """Quando viene selezionata una partita dalla lista"""
        match_id = item.data(Qt.ItemDataRole.UserRole)
        if match_id:
            self.match_id = match_id
            self._load_match(match_id)

    def _load_match(self, match_id: int):
        """Carica i dati del match e mostra la pagina di setup"""
        try:
            with self.db.session_scope() as session:
                match = session.query(Match).filter_by(id=match_id).first()

                if not match:
                    QMessageBox.critical(
                        self, "Errore", f"Partita {match_id} non trovata"
                    )
                    return

                self.current_match = {
                    "id": match.id,
                    "home_team_id": match.home_team_id,
                    "away_team_id": match.away_team_id,
                    "home_team_name": match.home_team.name if match.home_team else "?",
                    "away_team_name": match.away_team.name if match.away_team else "?",
                }

                # Aggiorna il label info
                date_str = match.date.strftime("%Y-%m-%d %H:%M") if match.date else "-"
                self.label_match_info.setText(
                    f"{self.current_match['home_team_name']} vs {self.current_match['away_team_name']} ({date_str})"
                )

                # Carica squadre
                self.teams = []
                if match.home_team:
                    self.teams.append(
                        {"id": match.home_team_id, "name": match.home_team.name}
                    )
                if match.away_team:
                    self.teams.append(
                        {"id": match.away_team_id, "name": match.away_team.name}
                    )

                # Inizializza stato roster per team
                self.team_selected_players = {team["id"]: {} for team in self.teams}
                self.initial_team_players = {team["id"]: set() for team in self.teams}
                self.team_change_events = {team["id"]: [] for team in self.teams}

                # Carica roster esistente raggruppato per team
                for mp in match.roster:
                    if mp.team_id not in self.team_selected_players:
                        continue
                    self.team_selected_players[mp.team_id][mp.player_id] = {
                        "number": mp.number,
                        "role": mp.role,
                        "team_id": mp.team_id,
                        "is_captain": bool(getattr(mp.player, "captain", False)),
                    }
                    self.initial_team_players[mp.team_id].add(mp.player_id)

                # Popola dropdown squadre
                self.combo_teams.blockSignals(True)
                self.combo_teams.clear()
                for team in self.teams:
                    self.combo_teams.addItem(team["name"], team["id"])
                self.combo_teams.blockSignals(False)

                # Mostra la pagina di setup
                self.stacked.setCurrentIndex(1)

                # Nuovo flusso guidato: sempre dalla prima squadra
                self.current_team_index = 0
                self.current_team_id = None
                self.selected_players = {}
                self._set_active_team(0, preserve_current=False)

        except Exception as e:
            print(f"❌ Errore caricamento partita: {e}")
            import traceback

            traceback.print_exc()

    def _persist_current_team_selection(self):
        """Persisti lo stato del team corrente nella struttura per-team."""
        if self.current_team_id is None:
            return
        self.team_selected_players[self.current_team_id] = {
            player_id: data.copy() for player_id, data in self.selected_players.items()
        }

    def _set_active_team(self, index: int, preserve_current: bool = True):
        """Imposta il team attivo nel flusso guidato roster."""
        if index < 0 or index >= len(self.teams):
            return

        if preserve_current:
            self._persist_current_team_selection()

        self.current_team_index = index
        team = self.teams[index]
        self.current_team_id = team["id"]

        # Mostra il team corrente nel combo (read-only)
        self.combo_teams.blockSignals(True)
        self.combo_teams.setCurrentIndex(index)
        self.combo_teams.blockSignals(False)

        # Carica selezione team corrente
        self.selected_players = {
            player_id: data.copy()
            for player_id, data in self.team_selected_players.get(
                self.current_team_id, {}
            ).items()
        }

        self._update_team_step_ui()
        self._load_team_players(self.current_team_id)
        self._update_roster_events_list()

    def _update_team_step_ui(self):
        """Aggiorna etichette e pulsante in base allo step corrente."""
        if not self.teams:
            self.label_current_team.setText("Squadra corrente: -")
            self.label_team_step.setText("Step roster: -")
            self.btn_continue.setText("Continua")
            self._update_roster_counter()
            return

        current_team_name = self.teams[self.current_team_index]["name"]
        self.label_current_team.setText(f"Squadra corrente: {current_team_name}")
        total = len(self.teams)
        step = self.current_team_index + 1
        self.label_team_step.setText(
            f"Step {step}/{total} - Configura roster: {current_team_name}"
        )

        if self.current_team_index < total - 1:
            next_team_name = self.teams[self.current_team_index + 1]["name"]
            self.btn_continue.setText(f"Continua → {next_team_name}")
        else:
            self.btn_continue.setText("Salva roster e apri formation")

        self._update_roster_counter()

    def _get_role_icon(self, role_name: str):
        """Ritorna l'icona del ruolo, se disponibile."""
        if get_role_icon is None:
            return None
        icon = get_role_icon(role_name or "", size=14)
        if icon.isNull():
            return None
        return icon

    def _is_dark_theme(self) -> bool:
        return self.palette().window().color().lightness() < 128

    def _muted_text_color(self) -> QColor:
        return QColor("#9D8878") if self._is_dark_theme() else QColor("#7D6757")

    def _base_text_color(self) -> QColor:
        return QColor("#F6EFE9") if self._is_dark_theme() else QColor("#2B211C")

    def _update_roster_counter(self):
        """Aggiorna il contatore giocatori caricati per la squadra corrente."""
        count = len(self.selected_players)
        max_count = self.MAX_PLAYERS_PER_TEAM

        self.label_roster_counter.setText(f"Giocatori caricati: {count}/{max_count}")
        if count > max_count:
            self.label_roster_counter.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #C7451A;"
            )
        elif count == max_count:
            self.label_roster_counter.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #E95420;"
            )
        else:
            self.label_roster_counter.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #8A613F;"
            )

    def _normalize_captains_for_current_team(self, captain_player_id: int | None):
        """Mantiene al massimo un capitano per il team corrente."""
        for player_id in list(self.selected_players.keys()):
            self.selected_players[player_id]["is_captain"] = (
                captain_player_id is not None and player_id == captain_player_id
            )

    def _build_player_event_text(self, player_id: int, action: str) -> str:
        """Costruisce la stringa evento per la timeline roster."""
        player_data = self.players_cache.get(player_id)
        if player_data:
            label = (
                f"#{player_data['number']} {player_data['first_name']} "
                f"{player_data['last_name']}"
            ).strip()
        else:
            label = f"Giocatore ID {player_id}"

        timestamp = datetime.now().strftime("%H:%M:%S")
        if action == "added":
            return f"[{timestamp}] Aggiunto: {label}"
        return f"[{timestamp}] Rimosso: {label}"

    def _log_roster_event(self, action: str, player_id: int):
        """Registra un evento di aggiunta/rimozione per il team corrente."""
        if self.current_team_id is None:
            return

        team_events = self.team_change_events.setdefault(self.current_team_id, [])
        team_events.append(
            {
                "action": action,
                "player_id": player_id,
                "text": self._build_player_event_text(player_id, action),
            }
        )
        self._update_roster_events_list()

    def _update_roster_events_list(self):
        """Aggiorna la lista eventi roster del team corrente."""
        self.list_roster_events.clear()

        if self.current_team_id is None:
            return

        events = self.team_change_events.get(self.current_team_id, [])
        if not events:
            info_item = QListWidgetItem("Nessuna modifica registrata")
            info_item.setForeground(self._muted_text_color())
            self.list_roster_events.addItem(info_item)
            return

        for event in events:
            item = QListWidgetItem(event["text"])
            if event.get("action") == "added":
                item.setForeground(QColor("#E95420"))
            elif event.get("action") == "removed":
                item.setForeground(QColor("#C7451A"))
            else:
                item.setForeground(self._base_text_color())
            self.list_roster_events.addItem(item)

    def _on_team_changed(self, index: int):
        """Quando cambia la squadra nel dropdown."""
        # Il cambio è guidato dal pulsante "Continua"; qui gestiamo solo casi programmatici.
        self._set_active_team(index)

    def _load_team_players(self, team_id: int):
        """Carica i giocatori di una squadra nella lista sinistra"""
        try:
            with self.db.session_scope() as session:
                players = (
                    session.query(Player)
                    .filter_by(team_id=team_id)
                    .order_by(Player.number)
                    .all()
                )

                # Cache dei dati dei giocatori
                self.players_cache = {}
                for player in players:
                    self.players_cache[player.id] = {
                        "id": player.id,
                        "first_name": player.first_name or "",
                        "last_name": player.last_name or "",
                        "number": player.number or 0,
                        "role": player.role or "Schiacciatore",
                        "team_id": player.team_id,
                        "captain": bool(getattr(player, "captain", False)),
                    }

                # Popola la lista disponibili
                self._update_available_players_list()

        except Exception as e:
            print(f"❌ Errore caricamento giocatori: {e}")

    def _update_available_players_list(self):
        """Aggiorna la lista dei giocatori disponibili"""
        self.list_available_players.clear()

        for player_id, player_data in self.players_cache.items():
            # Formato: "Nome Cognome (#numero, ruolo)" con evidenza capitano
            is_selected = player_id in self.selected_players
            is_captain = self.selected_players.get(player_id, {}).get(
                "is_captain", player_data.get("captain", False)
            )

            captain_suffix = " (C)" if is_captain else ""
            display_text = (
                f"{player_data['first_name']} {player_data['last_name']} "
                f"(#{player_data['number']}, {player_data['role'] or 'N/A'})"
                f"{captain_suffix}"
            ).strip()

            if is_selected:
                display_text = f"[In roster] {display_text}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, player_id)

            role_icon = self._get_role_icon(player_data.get("role", ""))
            if role_icon is not None:
                item.setIcon(role_icon)

            self.list_available_players.addItem(item)

        # Aggiorna la tabella del roster
        self._update_roster_table()

    def _on_available_player_selected(self):
        """Quando viene selezionato un giocatore nella lista disponibili"""
        # Potrebbe essere utilizzato per preview o altri scopi
        pass

    def _on_available_player_double_clicked(self, item: QListWidgetItem):
        """Double-click su giocatore disponibile = aggiungilo al roster"""
        player_id = item.data(Qt.ItemDataRole.UserRole)
        if player_id:
            self._add_player_to_roster(player_id)

    def _on_add_single_player(self):
        """Pulsante ➕ Single: Aggiungi il giocatore selezionato"""
        current_item = self.list_available_players.currentItem()
        if current_item:
            player_id = current_item.data(Qt.ItemDataRole.UserRole)
            if player_id:
                self._add_player_to_roster(player_id)
        else:
            QMessageBox.warning(self, "Attenzione", "Seleziona un giocatore")

    def _on_add_all_players(self):
        """Pulsante ➕ Tutti: Aggiungi tutti i giocatori della squadra"""
        count = self.list_available_players.count()
        added = 0
        for i in range(count):
            if len(self.selected_players) >= self.MAX_PLAYERS_PER_TEAM:
                break

            item = self.list_available_players.item(i)
            player_id = item.data(Qt.ItemDataRole.UserRole)
            if player_id and player_id not in self.selected_players:
                self._add_player_to_roster(player_id)
                added += 1

        if added == 0:
            QMessageBox.information(
                self, "Info", "Tutti i giocatori sono già nel roster o limite raggiunto"
            )

    def _add_player_to_roster(self, player_id: int):
        """Aggiunge un giocatore al roster"""
        if player_id in self.selected_players:
            QMessageBox.warning(self, "Attenzione", "Giocatore già nel roster")
            return

        if len(self.selected_players) >= self.MAX_PLAYERS_PER_TEAM:
            QMessageBox.warning(
                self,
                "Limite raggiunto",
                f"Non puoi superare {self.MAX_PLAYERS_PER_TEAM} giocatori in partita.",
            )
            return

        # Usa i dati dal cache
        if player_id in self.players_cache:
            player_data = self.players_cache[player_id]
            self.selected_players[player_id] = {
                "number": player_data["number"],
                "role": player_data["role"],
                "team_id": player_data["team_id"],
                "is_captain": bool(player_data.get("captain", False)),
            }

            # Se entra un capitano già marcato nel DB, mantieni unicità del capitano nel team
            if self.selected_players[player_id].get("is_captain"):
                self._normalize_captains_for_current_team(player_id)

            self._persist_current_team_selection()
            self._log_roster_event("added", player_id)
            self._update_available_players_list()
        else:
            QMessageBox.critical(self, "Errore", "Giocatore non trovato")

    def _on_remove_single_player(self):
        """Pulsante ➖ Single: Rimuovi il giocatore selezionato dal roster"""
        selected_row = self.table_roster.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona un giocatore dal roster")
            return

        player_id = self.table_roster.item(selected_row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        if player_id:
            self._remove_player_from_roster(player_id)

    def _remove_player_from_roster(self, player_id: int):
        """Rimuove un giocatore dal roster"""
        if player_id in self.selected_players:
            del self.selected_players[player_id]
            self._persist_current_team_selection()
            self._log_roster_event("removed", player_id)
            self._update_available_players_list()

    def _on_roster_item_double_clicked(self, item: QTableWidgetItem):
        """
        Double-click su un elemento della tabella del roster.
        Se è nella colonna Ruolo (2), apri il dialog di modifica.
        """
        row = item.row()
        col = item.column()

        # Ruolo (colonna 2)
        if col == 2:
            player_id = self.table_roster.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if player_id:
                self._edit_player(player_id)

    def _on_roster_table_item_changed(self, item: QTableWidgetItem):
        """Gestisce i cambiamenti inline della tabella roster (es. checkbox capitano)."""
        if self._updating_roster_table:
            return

        if item.column() != 3:
            return

        player_id = self.table_roster.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        if not player_id or player_id not in self.selected_players:
            return

        is_checked = item.checkState() == Qt.CheckState.Checked
        if is_checked:
            self._normalize_captains_for_current_team(player_id)
        else:
            self.selected_players[player_id]["is_captain"] = False

        self._persist_current_team_selection()
        self._update_available_players_list()

    def _update_roster_table(self):
        """Aggiorna la tabella del roster in base ai giocatori selezionati"""
        self._updating_roster_table = True
        self.table_roster.blockSignals(True)
        self.table_roster.setRowCount(len(self.selected_players))

        sorted_players = sorted(
            self.selected_players.items(),
            key=lambda item: (item[1].get("number", 0), item[0]),
        )

        row = 0
        for player_id, data in sorted_players:
            if player_id in self.players_cache:
                player_data = self.players_cache[player_id]
                first_name = player_data["first_name"]
                last_name = player_data["last_name"]
                role = data["role"]

                # Colonna Nome
                item_first = QTableWidgetItem(first_name if first_name else "")
                item_first.setFlags(item_first.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_first.setData(Qt.ItemDataRole.UserRole, player_id)
                self.table_roster.setItem(row, 0, item_first)

                # Colonna Cognome
                item_last = QTableWidgetItem(last_name if last_name else "")
                item_last.setFlags(item_last.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_roster.setItem(row, 1, item_last)

                # Colonna Ruolo con icona
                item_role = QTableWidgetItem(role if role else "")
                item_role.setFlags(item_role.flags() & ~Qt.ItemFlag.ItemIsEditable)
                role_icon = self._get_role_icon(role)
                if role_icon is not None:
                    item_role.setIcon(role_icon)
                self.table_roster.setItem(row, 2, item_role)

                # Colonna Capitano (checkbox)
                is_captain = bool(data.get("is_captain", False))
                item_captain = QTableWidgetItem("C")
                captain_icon = self._get_role_icon("capitano")
                if captain_icon is not None:
                    item_captain.setIcon(captain_icon)
                item_captain.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_captain.setFlags(
                    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
                )
                item_captain.setCheckState(
                    Qt.CheckState.Checked if is_captain else Qt.CheckState.Unchecked
                )
                self.table_roster.setItem(row, 3, item_captain)

                # Colonna Azioni (bottone delete)
                btn_delete = QPushButton("Rimuovi")
                btn_delete.setIcon(
                    self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
                )
                btn_delete.setMaximumWidth(98)
                btn_delete.setStyleSheet(
                    "background-color: #8A613F; color: white; border: 1px solid #6E4B32; border-radius: 5px;"
                )
                btn_delete.clicked.connect(
                    lambda checked, pid=player_id: self._remove_player_from_roster(pid)
                )
                self.table_roster.setCellWidget(row, 4, btn_delete)

                row += 1

        self.table_roster.blockSignals(False)
        self._updating_roster_table = False
        self._update_roster_counter()

    def _edit_player(self, player_id: int):
        """Apri un dialog per modificare numero/ruolo del giocatore"""
        if player_id not in self.selected_players:
            return

        if player_id not in self.players_cache:
            QMessageBox.critical(self, "Errore", "Giocatore non trovato")
            return

        data = self.selected_players[player_id]
        player_data = self.players_cache[player_id]
        current_number = data["number"]
        current_role = data["role"]
        current_captain = bool(data.get("is_captain", False))

        # Dialog di modifica
        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"Modifica - {player_data['first_name']} {player_data['last_name']}"
        )
        dialog.setModal(True)

        layout = QFormLayout(dialog)

        # Numero
        spin_number = QSpinBox()
        spin_number.setMinimum(0)
        spin_number.setMaximum(99)
        spin_number.setValue(current_number)
        layout.addRow("Numero Maglia:", spin_number)

        # Ruolo (dropdown)
        combo_role = QComboBox()
        roles = [
            "Palleggiatore",
            "Opposto",
            "Schiacciatore",
            "Banda",
            "Centrale",
            "Libero",
        ]
        combo_role.addItems(roles)
        if current_role in roles:
            combo_role.setCurrentText(current_role)
        layout.addRow("Ruolo:", combo_role)

        # Capitano
        check_captain = QCheckBox("Capitano")
        check_captain.setChecked(current_captain)
        layout.addRow("", check_captain)

        # Bottoni
        btn_ok = QPushButton("OK")
        btn_ok.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        )
        btn_cancel = QPushButton("Annulla")
        btn_cancel.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        )
        layout.addRow(btn_ok, btn_cancel)

        def on_ok():
            self.selected_players[player_id]["number"] = spin_number.value()
            self.selected_players[player_id]["role"] = combo_role.currentText()
            self.selected_players[player_id]["is_captain"] = check_captain.isChecked()

            if check_captain.isChecked():
                self._normalize_captains_for_current_team(player_id)

            self._persist_current_team_selection()
            self._update_available_players_list()
            dialog.accept()

        btn_ok.clicked.connect(on_ok)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec()

    def _go_back_to_selection(self):
        """Torna alla pagina di selezione partita"""
        self.selected_players = {}
        self.team_selected_players = {}
        self.initial_team_players = {}
        self.team_change_events = {}
        self.current_match = None
        self.current_team_id = None
        self.current_team_index = 0
        self.match_id = None
        self.players_cache = {}
        self.list_roster_events.clear()
        self.stacked.setCurrentIndex(0)

    def _save_all_teams_to_db(self):
        """Salva nel DB il roster completo di tutte le squadre del match."""
        self._persist_current_team_selection()

        if not self.current_match:
            raise ValueError("Nessun match caricato")

        match_id = self.current_match["id"]

        with self.db.session_scope() as session:
            # Elimina il vecchio roster
            session.query(MatchPlayer).filter_by(match_id=match_id).delete()

            # Aggiungi i giocatori di tutte le squadre
            for team in self.teams:
                team_id = team["id"]
                team_roster = self.team_selected_players.get(team_id, {})

                # Capitano a livello squadra (unico)
                captain_ids = [
                    pid for pid, pdata in team_roster.items() if pdata.get("is_captain")
                ]
                captain_id = captain_ids[0] if captain_ids else None

                # Aggiorna il flag capitano sui player del team
                session.query(Player).filter_by(team_id=team_id).update(
                    {Player.captain: False}, synchronize_session=False
                )
                if captain_id is not None:
                    player_obj = session.query(Player).filter_by(id=captain_id).first()
                    if player_obj is not None:
                        player_obj.captain = True

                for player_id, data in team_roster.items():
                    role = data.get("role") or ""
                    mp = MatchPlayer(
                        match_id=match_id,
                        player_id=player_id,
                        team_id=team_id,
                        number=data.get("number", 0),
                        role=role,
                        is_libero=(role.lower() == "libero"),
                        is_starter=False,
                    )
                    session.add(mp)

            session.flush()

    def _save_roster(self):
        """Salva il roster per step: prima squadra → seconda squadra → formation panel."""
        if not self.current_match:
            QMessageBox.warning(self, "Errore", "Nessuna partita selezionata")
            return

        current_team_name = (
            self.teams[self.current_team_index]["name"]
            if self.teams and self.current_team_index < len(self.teams)
            else "Squadra"
        )

        if not self.selected_players:
            QMessageBox.warning(
                self,
                "Errore",
                f"Seleziona almeno un giocatore per {current_team_name}",
            )
            return

        if len(self.selected_players) > self.MAX_PLAYERS_PER_TEAM:
            QMessageBox.warning(
                self,
                "Errore",
                f"{current_team_name}: massimo {self.MAX_PLAYERS_PER_TEAM} giocatori in partita.",
            )
            return

        self._persist_current_team_selection()

        # STEP INTERMEDIO: salva e passa alla squadra successiva
        if self.current_team_index < len(self.teams) - 1:
            try:
                self._save_all_teams_to_db()
            except Exception as e:
                print(f"❌ Errore salvataggio roster: {e}")
                import traceback

                traceback.print_exc()
                QMessageBox.critical(self, "Errore", f"Errore salvataggio: {e}")
                return

            next_index = self.current_team_index + 1
            next_team_name = self.teams[next_index]["name"]
            self._set_active_team(next_index, preserve_current=False)
            QMessageBox.information(
                self,
                "Roster salvato",
                f"Roster di {current_team_name} salvato.\n"
                f"Ora configura {next_team_name}.",
            )
            return

        # STEP FINALE: validazione completa (entrambe le squadre)
        for idx, team in enumerate(self.teams):
            team_roster = self.team_selected_players.get(team["id"], {})
            if not team_roster:
                self._set_active_team(idx, preserve_current=False)
                QMessageBox.warning(
                    self,
                    "Errore",
                    f"Completa il roster per {team['name']} prima di continuare.",
                )
                return

            if len(team_roster) > self.MAX_PLAYERS_PER_TEAM:
                self._set_active_team(idx, preserve_current=False)
                QMessageBox.warning(
                    self,
                    "Errore",
                    f"{team['name']}: massimo {self.MAX_PLAYERS_PER_TEAM} giocatori in partita.",
                )
                return

        try:
            self._save_all_teams_to_db()
            QMessageBox.information(
                self,
                "Successo",
                "Roster completo salvato con successo.\n"
                "Apro la pagina Formation Panel...",
            )

            # Emetti il signal solo quando tutto il flusso roster è completato
            self.roster_completed.emit()

            # Se parent è un dialog, chiudilo
            parent = self.parent()
            while parent:
                if isinstance(parent, QDialog):
                    parent.accept()
                    break
                parent = parent.parent()

        except Exception as e:
            print(f"❌ Errore salvataggio roster: {e}")
            import traceback

            traceback.print_exc()
            QMessageBox.critical(self, "Errore", f"Errore salvataggio: {e}")

"""
Volleyball Scout - Roster Setup Widget
Gestisce l'assegnazione dei giocatori a una partita
Con sistema di frecce per trasferimento giocatori tra disponibili e roster
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Ensure imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Match, MatchPlayer, Player


class RosterSetupWidget(QWidget):
    """Widget per configurare il roster di una partita con sistema frecce"""

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
        self.teams = []
        # {player_id: {"number": int, "role": str, "team_id": int}}
        self.selected_players = {}
        # Cache dei dati dei giocatori per evitare query ripetute
        self.players_cache = {}

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
        title = QLabel("📋 Roster Setup")
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
            btn_back = QPushButton("← Indietro")
            btn_back.setMaximumWidth(100)
            btn_back.clicked.connect(self._go_back_to_selection)
            header_layout.addWidget(btn_back)

        layout.addLayout(header_layout)

        # Sottotitolo team selector
        team_layout = QHBoxLayout()
        team_layout.addWidget(QLabel("Squadra:"))
        self.combo_teams = QComboBox()
        self.combo_teams.currentIndexChanged.connect(self._on_team_changed)
        team_layout.addWidget(self.combo_teams)
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

        btn_save = QPushButton("✅ Continua")
        btn_save.setMinimumWidth(150)
        btn_save.clicked.connect(self._save_roster)
        footer_layout.addWidget(btn_save)

        if not self.match_id:
            btn_cancel = QPushButton("❌ Annulla")
            btn_cancel.setMinimumWidth(150)
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
        self.list_available_players.setStyleSheet("""
            QListWidget::item {
                padding-top: 5px;
                padding-bottom: 5px;
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
        hint.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(hint)

        return widget

    def _create_arrow_buttons_section(self):
        """Crea la sezione centrale: Pulsanti Freccia"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addStretch()

        # Freccia verde singolo →
        self.btn_add_single = QPushButton("➕\nSingolo\n→")
        self.btn_add_single.setMinimumHeight(60)
        self.btn_add_single.clicked.connect(lambda: self._on_add_single_player())
        self.btn_add_single.setStyleSheet(
            """
            QPushButton {
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
                background-color: green;
                color: #333;
                border: 3px solid green;
                cursor: move;
            }
        """
        )
        layout.addWidget(self.btn_add_single)

        # Freccia verde tutti ⇒
        self.btn_add_all = QPushButton("➕\nTutti\n⇒")
        self.btn_add_all.setMinimumHeight(60)
        self.btn_add_all.clicked.connect(lambda: self._on_add_all_players())
        self.btn_add_all.setStyleSheet(
            """
            QPushButton {
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
                background-color: green;
                color: #333;
                border: 3px solid green;
                cursor: move;
            }
        """
        )
        layout.addWidget(self.btn_add_all)

        layout.addSpacing(20)

        # Freccia rossa singolo ←
        self.btn_remove_single = QPushButton("➖\nSingolo\n←")
        self.btn_remove_single.setMinimumHeight(60)
        self.btn_remove_single.clicked.connect(lambda: self._on_remove_single_player())
        self.btn_remove_single.setStyleSheet(
            """
            QPushButton {
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
                background-color: red;
                color: #333;
                border: 3px solid red;
                cursor: move;
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
        # Colonne: Nome, Cognome, Ruolo, Azioni (delete)
        self.table_roster = QTableWidget()
        self.table_roster.setColumnCount(4)
        self.table_roster.setHorizontalHeaderLabels(["Nome", "Cognome", "Ruolo", "❌"])
        self.table_roster.verticalHeader().setVisible(False)  # nasconde numeri di riga

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
        header.setSectionResizeMode(3, resize_to_contents)  # ❌

        self.table_roster.itemDoubleClicked.connect(self._on_roster_item_double_clicked)
        layout.addWidget(self.table_roster)
        return widget

    def load_matches(self):
        """Carica le partite dal database (modalità selezione)"""
        self.matches_list.clear()

        try:
            with self.db.session_scope() as session:
                matches = (
                    session.query(Match)
                    .filter(Match.status.in_(["draft", "in_progress"]))
                    .all()
                )

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

                # Popola dropdown squadre
                self.combo_teams.blockSignals(True)
                self.combo_teams.clear()
                for team in self.teams:
                    self.combo_teams.addItem(team["name"], team["id"])
                self.combo_teams.blockSignals(False)
                self.combo_teams.setCurrentIndex(0)

                # Carica il roster esistente della partita
                self.selected_players = {}
                for mp in match.roster:
                    self.selected_players[mp.player_id] = {
                        "number": mp.number,
                        "role": mp.role,
                        "team_id": mp.team_id,
                    }

                # Mostra la pagina di setup
                self.stacked.setCurrentIndex(1)

                # Carica i giocatori della prima squadra
                self._on_team_changed(0)

                # Aggiorna la tabella del roster
                self._update_roster_table()

        except Exception as e:
            print(f"❌ Errore caricamento partita: {e}")
            import traceback

            traceback.print_exc()

    def _on_team_changed(self, index: int):
        """Quando cambia la squadra nel dropdown"""
        if index < 0 or index >= len(self.teams):
            return

        team_id = self.combo_teams.itemData(index)
        self.current_team_id = team_id
        self._load_team_players(team_id)

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
                    }

                # Popola la lista disponibili
                self._update_available_players_list()

        except Exception as e:
            print(f"❌ Errore caricamento giocatori: {e}")

    def _update_available_players_list(self):
        """Aggiorna la lista dei giocatori disponibili"""
        self.list_available_players.clear()

        for player_id, player_data in self.players_cache.items():
            # Formato: "Nome Cognome (Numero, Ruolo)"
            display_text = (
                f"{player_data['first_name']} {player_data['last_name']} "
                f"(#{player_data['number']}, {player_data['role'] or 'N/A'})"
            )
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, player_id)

            # Se è già nel roster, evidenzia
            if player_id in self.selected_players:
                item.setBackground(item.background())

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
                self._update_roster_table()
                self._update_available_players_list()
        else:
            QMessageBox.warning(self, "Attenzione", "Seleziona un giocatore")

    def _on_add_all_players(self):
        """Pulsante ➕ Tutti: Aggiungi tutti i giocatori della squadra"""
        count = self.list_available_players.count()
        added = 0
        for i in range(count):
            item = self.list_available_players.item(i)
            player_id = item.data(Qt.ItemDataRole.UserRole)
            if player_id and player_id not in self.selected_players:
                self._add_player_to_roster(player_id)
                added += 1

        if added == 0:
            QMessageBox.information(
                self, "Info", "Tutti i giocatori sono già nel roster"
            )
        else:
            self._update_roster_table()
            self._update_available_players_list()

    def _add_player_to_roster(self, player_id: int):
        """Aggiunge un giocatore al roster"""
        if player_id in self.selected_players:
            QMessageBox.warning(self, "Attenzione", "Giocatore già nel roster")
            return

        # Usa i dati dal cache
        if player_id in self.players_cache:
            player_data = self.players_cache[player_id]
            self.selected_players[player_id] = {
                "number": player_data["number"],
                "role": player_data["role"],
                "team_id": player_data["team_id"],
            }
            self._update_roster_table()
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
            self._update_available_players_list()

    def _on_remove_all_players(self):
        """Pulsante ➖ Tutti: Rimuovi tutti i giocatori dal roster"""
        if len(self.selected_players) == 0:
            QMessageBox.information(self, "Info", "Il roster è già vuoto")
            return

        reply = QMessageBox.question(
            self,
            "Conferma",
            "Rimuovere tutti i giocatori dal roster?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.selected_players.clear()
            self._update_roster_table()

    def _remove_player_from_roster(self, player_id: int):
        """Rimuove un giocatore dal roster"""
        if player_id in self.selected_players:
            del self.selected_players[player_id]
            self._update_roster_table()

    def _on_roster_item_double_clicked(self, item: QTableWidgetItem):
        """
        Double-click su un elemento della tabella del roster.
        Se è nella colonna Numero (2) o Ruolo (3), apri il dialog di modifica.
        """
        row = item.row()
        col = item.column()

        # Numero (col 2) o Ruolo (col 3)
        if col in [2, 3]:
            player_id = self.table_roster.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if player_id:
                self._edit_player(player_id)

    def _update_roster_table(self):
        """Aggiorna la tabella del roster in base ai giocatori selezionati"""
        print(f"Aggiornamento tabella roster: {len(self.selected_players)} giocatori")
        self.table_roster.setRowCount(len(self.selected_players))

        row = 0
        for player_id, data in self.selected_players.items():
            if player_id in self.players_cache:
                player_data = self.players_cache[player_id]
                first_name = player_data["first_name"]
                last_name = player_data["last_name"]
                role = data["role"]

                print(f"Aggiunta riga {row}: {first_name} {last_name} - {role}")

                # Colonna Nome
                item_first = QTableWidgetItem(first_name if first_name else "")
                item_first.setFlags(item_first.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_first.setData(Qt.ItemDataRole.UserRole, player_id)
                self.table_roster.setItem(row, 0, item_first)

                # Colonna Cognome
                item_last = QTableWidgetItem(last_name if last_name else "")
                item_last.setFlags(item_last.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_roster.setItem(row, 1, item_last)

                # Colonna Ruolo
                item_role = QTableWidgetItem(role if role else "")
                item_role.setFlags(item_role.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_roster.setItem(row, 2, item_role)

                # Colonna Azioni (bottone delete)
                btn_delete = QPushButton("❌")
                btn_delete.setMaximumWidth(40)
                btn_delete.setStyleSheet("background-color: red; color: white;")
                btn_delete.clicked.connect(
                    lambda checked, pid=player_id: self._remove_player_from_roster(pid)
                )
                self.table_roster.setCellWidget(row, 3, btn_delete)

                row += 1

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

        # Bottoni
        btn_ok = QPushButton("✅ OK")
        btn_cancel = QPushButton("❌ Annulla")
        layout.addRow(btn_ok, btn_cancel)

        def on_ok():
            self.selected_players[player_id]["number"] = spin_number.value()
            self.selected_players[player_id]["role"] = combo_role.currentText()
            self._update_roster_table()
            dialog.accept()

        btn_ok.clicked.connect(on_ok)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec()

    def _go_back_to_selection(self):
        """Torna alla pagina di selezione partita"""
        self.selected_players = {}
        self.current_match = None
        self.current_team_id = None
        self.match_id = None
        self.players_cache = {}
        self.stacked.setCurrentIndex(0)

    def _save_roster(self):
        """Salva il roster nel database e passa alla squadra successiva o alla formation_panel"""
        if not self.current_match:
            QMessageBox.warning(self, "Errore", "Nessuna partita selezionata")
            return

        if not self.selected_players:
            QMessageBox.warning(self, "Errore", "Seleziona almeno un giocatore")
            return

        try:
            with self.db.session_scope() as session:
                # Elimina il vecchio roster
                session.query(MatchPlayer).filter_by(
                    match_id=self.current_match["id"]
                ).delete()

                # Aggiungi i nuovi giocatori
                for player_id, data in self.selected_players.items():
                    mp = MatchPlayer(
                        match_id=self.current_match["id"],
                        player_id=player_id,
                        team_id=data["team_id"],
                        number=data["number"],
                        role=data["role"],
                        is_libero=False,
                        is_starter=False,
                    )
                    session.add(mp)

                session.flush()

            QMessageBox.information(self, "Successo", "Roster salvato con successo! ✅")

            # Emetti il signal
            self.roster_completed.emit()

            # Passa alla squadra successiva o alla formation_panel
            if self.current_team_id == self.current_match["home_team_id"]:
                # Passa alla squadra away
                self.current_team_id = self.current_match["away_team_id"]
                self._load_team_players(self.current_team_id)
                self._update_roster_table()
            else:
                # Passa alla formation_panel
                from volleyball_scout.ui.formation_panel import FormationPanel

                self.formation_panel = FormationPanel(
                    db=self.db,
                    match_id=self.current_match["id"],
                    home_team_id=self.current_match["home_team_id"],
                    away_team_id=self.current_match["away_team_id"],
                    parent=self,
                )
                self.formation_panel.show()

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

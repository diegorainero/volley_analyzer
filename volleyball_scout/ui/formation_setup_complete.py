"""
Formation Setup Complete - Widget con Match Selector integrato
Gestisce la navigazione tra lista di partite e dettagli della formazione
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .formation_panel import FormationPanel
from .new_match_dialog import NewMatchDialog
from .roster_setup import RosterSetupWidget


class FormationSetupMatches(QWidget):
    """
    Widget per la selezione delle partite da elaborare.
    Emette un signal quando l'utente seleziona una partita.
    """

    # Signal emesso quando viene selezionato un match per la formazione
    match_selected = pyqtSignal(dict)  # Emette il match dict

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.matches = []
        self.parent_formation = parent  # Riferimento al FormationSetupComplete

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Titolo
        title = QLabel("🏐 Selezione Partita per Formazione")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Sottotitolo
        subtitle = QLabel("Clicca su una partita per inserire la formazione")
        subtitle.setStyleSheet("color: #999999; font-size: 12px;")
        layout.addWidget(subtitle)

        # Pulsante "Nuova Partita"
        btn_new_match = QPushButton("➕ Nuova Partita")
        btn_new_match.setMaximumWidth(150)
        btn_new_match.clicked.connect(self._on_new_match_clicked)
        layout.addWidget(btn_new_match)

        # Tabella match
        self.matches_table = QTableWidget()
        self.matches_table.setColumnCount(4)
        self.matches_table.setHorizontalHeaderLabels(["Home", "Away", "Data", "Status"])
        self.matches_table.setColumnWidth(0, 200)
        self.matches_table.setColumnWidth(1, 200)
        self.matches_table.setColumnWidth(2, 150)
        self.matches_table.setColumnWidth(3, 150)

        # Double-click per aprire formazione
        self.matches_table.itemDoubleClicked.connect(self._on_match_double_clicked)

        layout.addWidget(self.matches_table, 1)

        # Bottone refresh
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.setMaximumWidth(150)
        btn_refresh.clicked.connect(self._load_matches)
        layout.addWidget(btn_refresh)

        self.setLayout(layout)

        # Carica i match
        self._load_matches()

    def _load_matches(self):
        """Carica i match incompleti dal database"""
        try:
            self.matches = []
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import Match

                matches_data = (
                    session.query(Match)
                    .filter(Match.status.in_(["draft", "in_progress"]))
                    .all()
                )

                for match in matches_data:
                    home_name = match.home_team.name if match.home_team else "TBD"
                    away_name = match.away_team.name if match.away_team else "TBD"
                    self.matches.append(
                        {
                            "id": match.id,
                            "home_team": home_name,
                            "away_team": away_name,
                            "date": match.date,
                            "status": match.status,
                            "home_team_id": match.home_team_id,
                            "away_team_id": match.away_team_id,
                        }
                    )

            # Popola la tabella
            self.matches_table.setRowCount(len(self.matches))
            for idx, match in enumerate(self.matches):
                home_item = QTableWidgetItem(match["home_team"])
                away_item = QTableWidgetItem(match["away_team"])
                date_item = QTableWidgetItem(
                    match["date"].strftime("%Y-%m-%d %H:%M") if match["date"] else ""
                )
                status_item = QTableWidgetItem(match["status"])

                self.matches_table.setItem(idx, 0, home_item)
                self.matches_table.setItem(idx, 1, away_item)
                self.matches_table.setItem(idx, 2, date_item)
                self.matches_table.setItem(idx, 3, status_item)

            if len(self.matches) == 0:
                self.matches_table.setRowCount(1)
                msg_item = QTableWidgetItem(
                    "Nessuna partita da completare. Crea una nuova partita per iniziare."
                )
                self.matches_table.setItem(0, 0, msg_item)

        except Exception as e:
            print(f"⚠️ Error loading matches: {e}")
            import traceback

            traceback.print_exc()

    def _on_match_double_clicked(self, item):
        """Quando l'utente double-clicca su un match, emetti il signal"""
        current_row = self.matches_table.currentRow()
        if current_row >= 0 and current_row < len(self.matches):
            match = self.matches[current_row]
            self._on_match_selected(match)

    def _on_new_match_clicked(self):
        """Apri il dialog per creare una nuova partita"""
        dialog = NewMatchDialog(self.db, self)
        dialog.match_created.connect(self._on_new_match_created)
        dialog.exec()

    def _on_new_match_created(self, match_id: int):
        """Quando una nuova partita è stata creata, apri il RosterSetup"""
        if self.parent_formation:
            self.parent_formation._open_roster_setup(match_id)


class FormationSetupComplete(QWidget):
    """
    Widget principale per la gestione della formazione.
    Utilizza QStackedWidget per navigare tra lista match e dettagli della formazione.

    Index 0: FormationSetupMatches (lista partite)
    Index 1: FormationPanel (dettagli formazione)
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_match = None
        self.current_formation_panel = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # QStackedWidget per navigare tra le pagine
        self.stacked_widget = QStackedWidget()

        # Index 0: Lista di match
        self.matches_widget = FormationSetupMatches(self.db, parent=self)
        self.matches_widget.match_selected.connect(self._on_match_selected)
        self.stacked_widget.addWidget(self.matches_widget)

        # Index 1: FormationPanel (sarà aggiunto dinamicamente)
        self.stacked_widget.addWidget(QWidget())  # Placeholder per ora

        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Mostra la lista di match all'inizio
        self.stacked_widget.setCurrentIndex(0)

    def _on_match_selected(self, match):
        """
        Quando l'utente seleziona una partita, carica la formazione e naviga
        """
        self.current_match = match
        self._load_and_show_formation(match)

    def _load_and_show_formation(self, match):
        """
        Carica la FormationPanel per il match selezionato e la mostra
        """
        try:
            teams = []
            players_by_team = {}

            with self.db.session_scope() as session:
                from volleyball_scout.core.models import Player, Team

                # Carica home team
                if match["home_team_id"]:
                    home_team = (
                        session.query(Team).filter_by(id=match["home_team_id"]).first()
                    )
                    if home_team:
                        teams.append({"id": home_team.id, "name": home_team.name})
                        players = (
                            session.query(Player).filter_by(team_id=home_team.id).all()
                        )
                        players_by_team[home_team.id] = [
                            {
                                "id": p.id,
                                "number": p.number,
                                "last_name": p.last_name,
                                "role": p.role,
                            }
                            for p in players
                        ]

                # Carica away team
                if match["away_team_id"]:
                    away_team = (
                        session.query(Team).filter_by(id=match["away_team_id"]).first()
                    )
                    if away_team:
                        teams.append({"id": away_team.id, "name": away_team.name})
                        players = (
                            session.query(Player).filter_by(team_id=away_team.id).all()
                        )
                        players_by_team[away_team.id] = [
                            {
                                "id": p.id,
                                "number": p.number,
                                "last_name": p.last_name,
                                "role": p.role,
                            }
                            for p in players
                        ]

            # Crea la FormationPanel
            if teams:
                # Rimuovi la vecchia FormationPanel se esiste
                if self.current_formation_panel is not None:
                    widget = self.stacked_widget.widget(1)
                    if widget:
                        self.stacked_widget.removeWidget(widget)
                        widget.deleteLater()

                # Crea e configura la nuova FormationPanel
                self.current_formation_panel = FormationPanel(
                    teams,
                    players_by_team,
                    matches=self.matches_widget.matches,
                )
                self.current_formation_panel.match_id = match["id"]

                # Connetti il segnale per tornare alla lista
                self.current_formation_panel.back_requested.connect(
                    self._on_back_to_matches
                )

                # Aggiungi il widget al stacked widget (index 1)
                self.stacked_widget.addWidget(self.current_formation_panel)
                self.stacked_widget.setCurrentIndex(1)
            else:
                print(f"⚠️ Match {match['id']} non ha squadre associate")

        except Exception as e:
            print(f"⚠️ Error loading formation: {e}")
            import traceback

            traceback.print_exc()

    def _on_back_to_matches(self):
        """
        Quando l'utente clicca il pulsante "Indietro", torna alla lista di match
        """
        self.stacked_widget.setCurrentIndex(0)
        # Aggiorna la lista
        self.matches_widget._load_matches()

    def _open_roster_setup(self, match_id: int):
        """
        Apri il dialog RosterSetup per il match_id specificato.
        Dopo il completamento del roster, caricherà automaticamente la formazione.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("🏐 Setup Roster Partita")
        dialog.setModal(True)
        dialog.setMinimumSize(1000, 600)

        layout = QVBoxLayout(dialog)
        roster_widget = RosterSetupWidget(self.db, match_id=match_id, parent=dialog)

        layout.addWidget(roster_widget)
        dialog.setLayout(layout)

        # Quando il roster è completato, carica la formazione
        def on_roster_completed():
            # Ricarica i match
            self.matches_widget._load_matches()
            # Trova il match e carica la formazione
            for match in self.matches_widget.matches:
                if match["id"] == match_id:
                    self._on_match_selected(match)  # Chiama direttamente il metodo
                    break

        roster_widget.roster_completed.connect(on_roster_completed)

        # Mostra il dialog
        dialog.exec()

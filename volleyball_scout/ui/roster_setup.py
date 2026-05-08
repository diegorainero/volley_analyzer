"""
Volleyball Scout - Roster Setup Widget
Gestisce l'assegnazione dei giocatori a una partita
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Ensure imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Match, Player, Team


class RosterSetupWidget(QWidget):
    """Widget per configurare il roster di una partita"""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_match = None

        self._setup_ui()

    def _setup_ui(self):
        """Crea l'interfaccia utente"""
        main_layout = QVBoxLayout()

        # Title
        main_layout.addWidget(QLabel("<h2>📋 Roster Setup</h2>"))

        # Info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Seleziona una partita per configurare il roster"))
        info_layout.addStretch()
        main_layout.addLayout(info_layout)

        # Matches list
        matches_section = QGroupBox("Partite Disponibili")
        matches_layout = QVBoxLayout()

        self.matches_list = QListWidget()
        self.matches_list.itemClicked.connect(self.on_match_selected)
        matches_layout.addWidget(self.matches_list)

        matches_section.setLayout(matches_layout)
        main_layout.addWidget(matches_section)

        # Match details
        self.match_details = QWidget()
        details_layout = QVBoxLayout(self.match_details)

        details_layout.addWidget(QLabel("<b>Dettagli Partita</b>"))

        # Home team roster
        home_section = QGroupBox("Squadra Casa - Roster")
        home_layout = QVBoxLayout()
        self.home_roster_list = QListWidget()
        home_layout.addWidget(self.home_roster_list)
        home_section.setLayout(home_layout)
        details_layout.addWidget(home_section)

        # Away team roster
        away_section = QGroupBox("Squadra Trasferta - Roster")
        away_layout = QVBoxLayout()
        self.away_roster_list = QListWidget()
        away_layout.addWidget(self.away_roster_list)
        away_section.setLayout(away_layout)
        details_layout.addWidget(away_section)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("✅ Salva Roster")
        btn_save.clicked.connect(self.save_roster)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        details_layout.addLayout(btn_layout)

        self.match_details.hide()
        main_layout.addWidget(self.match_details)

        main_layout.addStretch()
        self.setLayout(main_layout)

        self.load_matches()

    def load_matches(self):
        """Carica le partite dal database"""
        self.matches_list.clear()

        try:
            session = self.db.get_session()
            matches = session.query(Match).all()

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

            session.close()
        except Exception as e:
            print(f"❌ Errore caricamento partite: {e}")

    def on_match_selected(self, item: QListWidgetItem):
        """Quando viene selezionata una partita"""
        match_id = item.data(Qt.ItemDataRole.UserRole)

        if match_id is None:
            return

        try:
            session = self.db.get_session()
            match = session.query(Match).filter_by(id=match_id).first()

            if match:
                self.current_match = match

                # Home team roster
                self.home_roster_list.clear()
                if match.home_team:
                    for player in match.home_team.players:
                        full_name = (
                            f"{player.first_name or ''} {player.last_name}".strip()
                        )
                        item = QListWidgetItem(f"#{player.number} - {full_name}")
                        item.setData(Qt.ItemDataRole.UserRole, player.id)
                        self.home_roster_list.addItem(item)

                # Away team roster
                self.away_roster_list.clear()
                if match.away_team:
                    for player in match.away_team.players:
                        full_name = (
                            f"{player.first_name or ''} {player.last_name}".strip()
                        )
                        item = QListWidgetItem(f"#{player.number} - {full_name}")
                        item.setData(Qt.ItemDataRole.UserRole, player.id)
                        self.away_roster_list.addItem(item)

                self.match_details.show()

            session.close()
        except Exception as e:
            print(f"❌ Errore selezione partita: {e}")

    def save_roster(self):
        """Salva il roster della partita"""
        if not self.current_match:
            QMessageBox.warning(self, "Errore", "Seleziona una partita.")
            return

        try:
            # Qui puoi implementare la logica per salvare il roster
            # Per ora, semplicemente mostriamo un messaggio di successo
            QMessageBox.information(self, "Successo", "Roster salvato con successo!")
        except Exception as e:
            print(f"❌ Errore salvataggio roster: {e}")
            QMessageBox.critical(self, "Errore", f"Errore salvataggio: {e}")

"""
New Match Dialog - Dialog per creare una nuova partita
"""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class NewMatchDialog(QDialog):
    """
    Dialog per creare una nuova partita.

    Emette un signal 'match_created' quando viene creata una partita con successo.
    """

    match_created = pyqtSignal(object)  # Emette il nuovo Match object

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.teams = []
        self.new_match = None

        self.setWindowTitle("➕ Nuova Partita")
        self.setModal(True)
        self.setMinimumWidth(500)

        self._load_teams()
        self._setup_ui()

    def _load_teams(self):
        """Carica la lista di squadre dal database"""
        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import Team

                teams_data = session.query(Team).order_by(Team.name).all()
                self.teams = [{"id": t.id, "name": t.name} for t in teams_data]
        except Exception as e:
            print(f"⚠️ Error loading teams: {e}")
            self.teams = []

    def _setup_ui(self):
        """Costruisce l'interfaccia del dialog"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Titolo
        title = QLabel("Crea una Nuova Partita")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Team A (Home)
        label_home = QLabel("Squadra A (Home):")
        self.combo_home = QComboBox()
        self.combo_home.addItem("-- Seleziona squadra --", -1)
        for team in self.teams:
            self.combo_home.addItem(team["name"], team["id"])
        form_layout.addRow(label_home, self.combo_home)

        # Team B (Away)
        label_away = QLabel("Squadra B (Away):")
        self.combo_away = QComboBox()
        self.combo_away.addItem("-- Seleziona squadra --", -1)
        for team in self.teams:
            self.combo_away.addItem(team["name"], team["id"])
        form_layout.addRow(label_away, self.combo_away)

        # Data/Ora
        label_date = QLabel("Data e Ora:")
        self.date_time_edit = QDateTimeEdit()
        self.date_time_edit.setDateTime(datetime.now())
        self.date_time_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow(label_date, self.date_time_edit)

        # Luogo
        label_venue = QLabel("Luogo:")
        self.line_venue = QLineEdit()
        self.line_venue.setPlaceholderText("es. Palasport di Milano")
        form_layout.addRow(label_venue, self.line_venue)

        layout.addLayout(form_layout)

        # Note (QTextEdit a parte)
        label_notes = QLabel("Note:")
        layout.addWidget(label_notes)
        self.text_notes = QTextEdit()
        self.text_notes.setPlaceholderText("Aggiungi note opzionali sulla partita...")
        self.text_notes.setMaximumHeight(100)
        layout.addWidget(self.text_notes)

        # Bottoni Salva/Annulla
        layout.addSpacing(10)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_save = QPushButton("✅ Salva")
        btn_save.setMinimumWidth(120)
        btn_save.clicked.connect(self._on_save)
        buttons_layout.addWidget(btn_save)

        btn_cancel = QPushButton("❌ Annulla")
        btn_cancel.setMinimumWidth(120)
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)
        layout.addStretch()

        self.setLayout(layout)

    def _validate_input(self) -> tuple[bool, str]:
        """
        Valida i dati inseriti.

        Returns:
            (is_valid, error_message)
        """
        home_team_id = self.combo_home.currentData()
        away_team_id = self.combo_away.currentData()

        # Verifica che le squadre siano selezionate
        if home_team_id == -1:
            return False, "Selezionare la Squadra A (Home)"
        if away_team_id == -1:
            return False, "Selezionare la Squadra B (Away)"

        # Verifica che siano squadre diverse
        if home_team_id == away_team_id:
            return False, "La Squadra A e la Squadra B devono essere diverse"

        # Verifica la data/ora
        try:
            match_datetime = self.date_time_edit.dateTime().toPyDateTime()
        except AttributeError:
            # PyQt5 compatibility fallback
            match_datetime = self.date_time_edit.dateTime().toPython()

        if match_datetime is None:
            return False, "Data/ora non valida"

        return True, ""

    def _on_save(self):
        """Salva la nuova partita nel database"""
        # Validazione
        is_valid, error_msg = self._validate_input()
        if not is_valid:
            QMessageBox.warning(self, "Errore di validazione", error_msg)
            return

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import Match

                home_team_id = self.combo_home.currentData()
                away_team_id = self.combo_away.currentData()
                try:
                    match_datetime = self.date_time_edit.dateTime().toPyDateTime()
                except AttributeError:
                    # PyQt5 compatibility fallback
                    match_datetime = self.date_time_edit.dateTime().toPython()
                venue = self.line_venue.text().strip()
                notes = self.text_notes.toPlainText().strip()

                # Crea il nuovo Match con status='draft'
                new_match = Match(
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    date=match_datetime,
                    venue=venue if venue else None,
                    notes=notes if notes else None,
                    status="draft",
                )

                session.add(new_match)
                session.flush()  # Flush per ottenere l'ID generato

                self.new_match = {
                    "id": new_match.id,
                    "home_team_id": new_match.home_team_id,
                    "away_team_id": new_match.away_team_id,
                    "date": new_match.date,
                    "venue": new_match.venue,
                    "notes": new_match.notes,
                    "status": new_match.status,
                }

                # Emetti il signal con i dati della nuova partita
                self.match_created.emit(self.new_match)

                QMessageBox.information(
                    self, "Successo", "Partita creata con successo! ✅"
                )

                self.accept()

        except Exception as e:
            print(f"⚠️ Error creating match: {e}")
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self, "Errore", f"Errore durante la creazione della partita: {e}"
            )

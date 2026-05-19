"""
MatchesGridWidget - Widget per visualizzare i match in una griglia con colori diversi in base allo stato
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    from volleyball_scout.core.database import DatabaseManager
    from volleyball_scout.core.models import Match
except ImportError:
    # Fallback per import relativi
    from ..core.database import DatabaseManager
    from ..core.models import Match


class MatchCardWidget(QFrame):
    """Card singolo match cliccabile"""

    clicked = pyqtSignal(int)  # match_id

    def __init__(self, match, parent=None):
        """Inizializza card match."""
        super().__init__(parent)
        self.match_id = match.id
        self.status = match.status

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Data
        date_str = match.date.strftime("%d/%m/%Y") if match.date else "Data Sconosciuta"
        date_label = QLabel(date_str)
        date_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(date_label)

        # Teams
        home_name = match.home_team.name if match.home_team else "Sconosciuta"
        away_name = match.away_team.name if match.away_team else "Sconosciuta"
        teams_label = QLabel(f"{home_name}\nvs\n{away_name}")
        teams_label.setFont(QFont("Arial", 9))
        teams_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(teams_label)

        # Status
        status_text = {
            "draft": "🔲 Bozza",
            "in_progress": "⏳ In Corso",
            "completed": "✅ Completato",
        }.get(match.status, match.status)
        status_label = QLabel(status_text)
        status_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)

        self.setLayout(layout)

        # Stile in base allo stato
        self._apply_status_style()

    def _apply_status_style(self):
        """Applica il colore di background in base allo stato"""
        colors = {
            "draft": "#E8E8E8",  # Grigio chiaro
            "in_progress": "#FFFACD",  # Giallo chiaro
            "completed": "#C8E6C9",  # Verde chiaro
        }
        bg_color = colors.get(self.status, "#FFFFFF")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid #333;
                border-radius: 6px;
                padding: 10px;
            }}
            QFrame:hover {{
                border: 2px solid #0066CC;
                background-color: {self._lighten_color(bg_color)};
            }}
        """)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _lighten_color(self, color: str) -> str:
        """Schiarisce un colore hex per l'effetto hover"""
        return color

    def mousePressEvent(self, event):
        """Gestisce il click sul card"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.match_id)
        super().mousePressEvent(event)


class MatchesGridWidget(QWidget):
    """Widget che mostra i match in una griglia scrollabile"""

    match_selected = pyqtSignal(int)  # match_id

    def __init__(self, db_manager, parent=None):
        """Inizializza widget griglia match."""
        super().__init__(parent)
        self.db = db_manager

        # Setup layout principale
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Titolo
        title = QLabel("📋 Tutti i Match")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Sottotitolo
        subtitle = QLabel("Clicca su un match per aprire lo scout")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(subtitle)

        # Scroll area con griglia
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        grid_widget.setLayout(self.grid_layout)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

        self.setLayout(layout)

        # Empty state
        self.empty_label = QLabel(
            "Nessun match presente.\nClicca su 'Nuovo Incontro' per crearne uno!"
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #999; font-style: italic; margin: 20px;")
        self.empty_label.hide()

        self.load_matches()

    def load_matches(self):
        """Carica tutti i match dal database e popola la griglia"""
        # Pulisci la griglia
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        with self.db.session_scope() as session:
            # Carica tutti i match, ordinati per data decrescente
            matches = session.query(Match).order_by(Match.date.desc()).all()

            if not matches:
                self.empty_label.show()
                return
            else:
                self.empty_label.hide()

            # Aggiungi i match alla griglia (max 4 colonne)
            row, col = 0, 0
            max_cols = 4

            for match in matches:
                card = MatchCardWidget(match)
                card.clicked.connect(self._on_match_clicked)
                self.grid_layout.addWidget(card, row, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            # Aggiungi stretch alla fine per pushare tutto verso l'alto
            if row > 0:
                self.grid_layout.setRowStretch(row, 1)

    def _on_match_clicked(self, match_id: int):
        """Emette il segnale quando si clicca su un match"""
        self.match_selected.emit(match_id)

    def refresh(self):
        """Ricarica la lista di match"""
        self.load_matches()

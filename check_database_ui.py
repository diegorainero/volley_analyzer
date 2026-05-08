#!/usr/bin/env python3
"""
Database Check UI - Visualizza squadre e giocatori dal database
Una GUI PyQt6 per inspezionare i dati senza dipendenze esterne.
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Match, Player, Team


class DatabaseCheckUI(QMainWindow):
    """UI per verificare i dati nel database."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏐 Database Scout - Verificatore Squadre e Giocatori")
        self.setGeometry(100, 100, 1400, 800)

        # Database
        try:
            self.db = DatabaseManager()
            self.db_connected = self.db.ping()
        except Exception as e:
            self.db = None
            self.db_connected = False
            print(f"❌ Errore database: {e}")

        # Main layout
        main_widget = QWidget()
        layout = QVBoxLayout()

        # Header con info database
        header = QLabel()
        if self.db_connected:
            db_info = self.db.get_db_info()
            header.setText(
                f"✅ Database connesso: {db_info['type']} ({db_info['url_safe']})"
            )
            header.setStyleSheet(
                "color: green; font-weight: bold; font-size: 12px; padding: 10px;"
            )
        else:
            header.setText("❌ Errore: Impossibile connettere il database")
            header.setStyleSheet(
                "color: red; font-weight: bold; font-size: 12px; padding: 10px;"
            )
        layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        if self.db_connected:
            # Tab 1: Squadre
            self.create_teams_tab()

            # Tab 2: Giocatori
            self.create_players_tab()

            # Tab 3: Partite
            self.create_matches_tab()

        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Aggiorna Dati")
        refresh_btn.clicked.connect(self.refresh_all)
        refresh_layout.addStretch()
        refresh_layout.addWidget(refresh_btn)
        layout.addLayout(refresh_layout)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Load data
        if self.db_connected:
            self.refresh_all()

    def create_teams_tab(self):
        """Crea il tab delle squadre."""
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel("📊 SQUADRE")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        self.teams_table = QTableWidget()
        self.teams_table.setColumnCount(5)
        self.teams_table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Categoria", "Impianto", "Giocatori"]
        )
        self.teams_table.horizontalHeader().setStretchLastSection(False)
        layout.addWidget(self.teams_table)

        widget.setLayout(layout)
        self.tabs.addTab(widget, "Squadre")

    def create_players_tab(self):
        """Crea il tab dei giocatori."""
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel("👥 GIOCATORI")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        self.players_table = QTableWidget()
        self.players_table.setColumnCount(7)
        self.players_table.setHorizontalHeaderLabels(
            ["Squadra", "#", "Nome", "Cognome", "Ruolo", "Libero", "Capitano"]
        )
        layout.addWidget(self.players_table)

        widget.setLayout(layout)
        self.tabs.addTab(widget, "Giocatori")

    def create_matches_tab(self):
        """Crea il tab delle partite."""
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel("🏐 PARTITE")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        self.matches_table = QTableWidget()
        self.matches_table.setColumnCount(5)
        self.matches_table.setHorizontalHeaderLabels(
            ["ID", "Casa", "Trasferta", "Data", "Stato"]
        )
        layout.addWidget(self.matches_table)

        widget.setLayout(layout)
        self.tabs.addTab(widget, "Partite")

    def refresh_all(self):
        """Aggiorna i dati da tutti i tab."""
        if not self.db_connected:
            return

        self.refresh_teams()
        self.refresh_players()
        self.refresh_matches()

    def refresh_teams(self):
        """Aggiorna il tab squadre."""
        try:
            session = self.db.get_session()
            teams = session.query(Team).all()

            self.teams_table.setRowCount(len(teams))

            for row, team in enumerate(teams):
                player_count = session.query(Player).filter_by(team_id=team.id).count()

                self.teams_table.setItem(row, 0, QTableWidgetItem(str(team.id)))
                self.teams_table.setItem(row, 1, QTableWidgetItem(team.name))
                self.teams_table.setItem(row, 2, QTableWidgetItem(team.category or "-"))
                self.teams_table.setItem(row, 3, QTableWidgetItem(team.venue or "-"))
                self.teams_table.setItem(row, 4, QTableWidgetItem(str(player_count)))

            # Ridimensiona colonne
            self.teams_table.resizeColumnsToContents()

            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel caricamento squadre: {e}")

    def refresh_players(self):
        """Aggiorna il tab giocatori."""
        try:
            session = self.db.get_session()
            teams = session.query(Team).all()

            all_players = []
            for team in teams:
                players = session.query(Player).filter_by(team_id=team.id).all()
                for player in players:
                    all_players.append(
                        {
                            "team_name": team.name,
                            "number": player.number,
                            "first_name": player.first_name or "",
                            "last_name": player.last_name,
                            "role": player.role or "-",
                            "is_libero": player.is_libero,
                            "captain": player.captain,
                        }
                    )

            self.players_table.setRowCount(len(all_players))

            for row, player in enumerate(all_players):
                self.players_table.setItem(
                    row, 0, QTableWidgetItem(player["team_name"])
                )
                self.players_table.setItem(
                    row, 1, QTableWidgetItem(str(player["number"]))
                )
                self.players_table.setItem(
                    row, 2, QTableWidgetItem(player["first_name"])
                )
                self.players_table.setItem(
                    row, 3, QTableWidgetItem(player["last_name"])
                )
                self.players_table.setItem(row, 4, QTableWidgetItem(player["role"]))
                self.players_table.setItem(
                    row, 5, QTableWidgetItem("✓" if player["is_libero"] else "")
                )
                self.players_table.setItem(
                    row, 6, QTableWidgetItem("✓" if player["captain"] else "")
                )

            self.players_table.resizeColumnsToContents()

            session.close()
        except Exception as e:
            QMessageBox.critical(
                self, "Errore", f"Errore nel caricamento giocatori: {e}"
            )

    def refresh_matches(self):
        """Aggiorna il tab partite."""
        try:
            session = self.db.get_session()
            matches = session.query(Match).all()

            self.matches_table.setRowCount(len(matches))

            for row, match in enumerate(matches):
                home = match.home_team.name if match.home_team else "?"
                away = match.away_team.name if match.away_team else "?"
                date_str = match.date.strftime("%Y-%m-%d %H:%M") if match.date else "-"

                self.matches_table.setItem(row, 0, QTableWidgetItem(str(match.id)))
                self.matches_table.setItem(row, 1, QTableWidgetItem(home))
                self.matches_table.setItem(row, 2, QTableWidgetItem(away))
                self.matches_table.setItem(row, 3, QTableWidgetItem(date_str))
                self.matches_table.setItem(
                    row, 4, QTableWidgetItem(match.status or "draft")
                )

            self.matches_table.resizeColumnsToContents()

            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel caricamento partite: {e}")


def main():
    app = QApplication(sys.argv)
    window = DatabaseCheckUI()
    window.show()

    print("=" * 80)
    print("🏐 DATABASE CHECK UI")
    print("=" * 80)
    print("\n✅ UI aperta per verificare i dati nel database")
    print("   - Squadre: visualizza tutte le squadre e il numero di giocatori")
    print("   - Giocatori: visualizza tutti i giocatori per squadra")
    print("   - Partite: visualizza tutte le partite registrate\n")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main() or 0)

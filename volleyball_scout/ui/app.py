"""
Volleyball Scout - Main PyQt6 Application with Integrated Menu Navigation
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Try importing all modules - use fallbacks where needed
try:
    from volleyball_scout.core.database import DatabaseManager
except ImportError:
    try:
        from core.database import DatabaseManager
    except ImportError as e:
        print(f"❌ Cannot import DatabaseManager: {e}")
        raise


# Import UI components with error handling
try:
    from volleyball_scout.ui.formation_setup_complete import FormationSetupComplete
except ImportError:
    try:
        from .formation_setup_complete import FormationSetupComplete
    except ImportError as e:
        print(f"⚠️ Warning: FormationSetupComplete not available: {e}")
        FormationSetupComplete = None

try:
    from volleyball_scout.ui.formation_panel import FormationPanel
except ImportError:
    try:
        from .formation_panel import FormationPanel
    except ImportError as e:
        print(f"⚠️ Warning: FormationPanel not available: {e}")
        FormationPanel = None


try:
    from volleyball_scout.core.models import Player, Team
    from volleyball_scout.ui.team_management import TeamManagementWidget
except ImportError:
    try:
        from ..core.models import Player, Team
        from .team_management import TeamManagementWidget
    except ImportError as e:
        print(f"⚠️ Warning: TeamManagementWidget not available: {e}")
        TeamManagementWidget = None
        Team = None
        Player = None

try:
    from volleyball_scout.ui.matches_grid import MatchesGridWidget
except ImportError:
    try:
        from .matches_grid import MatchesGridWidget
    except ImportError as e:
        print(f"⚠️ Warning: MatchesGridWidget not available: {e}")
        MatchesGridWidget = None

try:
    from volleyball_scout.ui.roster_setup import RosterSetupWidget
except ImportError:
    RosterSetupWidget = None  # Will create placeholder if not available


try:
    from volleyball_scout.ui.scout_panel import ScoutPanel
except ImportError:
    try:
        from .scout_panel import ScoutPanel
    except ImportError as e:
        print(f"⚠️ Warning: ScoutPanel not available: {e}")
        ScoutPanel = None


try:
    from volleyball_scout.ui.stats_view import StatsView
except ImportError:
    try:
        from .stats_view import StatsView
    except ImportError as e:
        print(f"⚠️ Warning: StatsView not available: {e}")
        StatsView = None


try:
    from volleyball_scout.ui.video_player import VideoPlayer
except ImportError:
    try:
        from .video_player import VideoPlayer
    except ImportError as e:
        print(f"⚠️ Warning: VideoPlayer not available: {e}")
        VideoPlayer = None

# Assets (icone web)
try:
    from volleyball_scout.ui.assets import get_section_icon
except ImportError:
    try:
        from .assets import get_section_icon
    except ImportError:
        get_section_icon = None


try:
    from volleyball_scout.ui.drafts.draft_widget import DraftListWidget
except ImportError:
    try:
        from .drafts.draft_widget import DraftListWidget
    except ImportError as e:
        print(f"⚠️ Warning: DraftListWidget not available: {e}")
        DraftListWidget = None


# Simple placeholder widgets
class PlaceholderWidget(QWidget):
    def __init__(self, title="Coming Soon", parent=None):
        # Inizializza il widget segnaposto con un titolo.
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<h2>{title}</h2>"))
        layout.addStretch()
        self.setLayout(layout)


# Placeholder for RosterSetupWidget if not available
if RosterSetupWidget is None:

    class RosterSetupWidget(QWidget):
        def __init__(self, db_manager, parent=None):
            # Inizializza il widget segnaposto per la gestione incontri.
            super().__init__(parent)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("🧾 Gestione incontri (non ancora implementato)"))
            layout.addStretch()
            self.setLayout(layout)


class DashboardView(QWidget):
    """Main dashboard with matches and drafts"""

    match_selected = pyqtSignal(int)
    draft_resumed = pyqtSignal(int)

    def __init__(self, db_manager, parent=None):
        # Inizializza la dashboard con griglia match e bozze.
        super().__init__(parent)
        self.db = db_manager

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Left panel: Matches Grid
        left_layout = QVBoxLayout()

        if MatchesGridWidget:
            self.matches_grid = MatchesGridWidget(db_manager)
            self.matches_grid.match_selected.connect(self._on_match_selected)
            left_layout.addWidget(self.matches_grid)
        else:
            left_layout.addWidget(QLabel("Matches grid not available"))

        layout.addLayout(left_layout, 1)

        # Right panel: Drafts
        right_layout = QVBoxLayout()
        right_label = QLabel("<h2>📝 Sessioni in Bozza</h2>")
        right_layout.addWidget(right_label)

        if DraftListWidget:
            try:
                self.drafts_widget = DraftListWidget(db_manager)
                self.drafts_widget.draft_resumed.connect(self._on_draft_resumed)
                right_layout.addWidget(self.drafts_widget)
            except Exception as e:
                print(f"⚠️ Error creating DraftListWidget: {e}")
                right_layout.addWidget(QLabel("Drafts widget error"))
        else:
            right_layout.addWidget(QLabel("Drafts widget not available"))

        layout.addLayout(right_layout, 1)

        self.setLayout(layout)

    def _on_match_selected(self, match_id: int):
        """Gestisce la selezione di un match"""
        self.match_selected.emit(match_id)

    def _on_draft_resumed(self, match_id: int):
        """Gestisce la ripresa di una bozza"""
        self.draft_resumed.emit(match_id)

    def refresh(self):
        """Aggiorna entrambi i widget"""
        if MatchesGridWidget and hasattr(self, "matches_grid"):
            self.matches_grid.load_matches()
        if DraftListWidget and hasattr(self, "drafts_widget"):
            self.drafts_widget.load_drafts()


class NavigationMenu(QWidget):
    """Menu di navigazione laterale con pulsanti per le sezioni"""

    section_selected = pyqtSignal(str)  # section name

    def __init__(self, parent=None):
        # Inizializza il menu di navigazione laterale.
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(8)

        # Titolo menu
        title = QLabel("🏐 SCOUT")
        title_font = QFont("Arial", 12, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)

        # Separatore
        separator = QLabel("─" * 20)
        layout.addWidget(separator)

        # Sezioni disponibili
        sections = [
            ("🏠 Dashboard", "dashboard"),
            ("👥 Squadre e Giocatori", "teams"),
            ("🧾 Gestione incontri", "roster"),
            ("🏐 Formazioni", "formation"),
            ("📡 Scouting Live", "scout"),
            ("📈 Statistiche", "stats"),
        ]

        self.buttons = {}
        for icon_text, section_id in sections:
            btn = QPushButton(icon_text)
            btn.setMinimumHeight(35)
            if callable(get_section_icon):
                icon = get_section_icon(section_id, size=16)
                if not icon.isNull():
                    btn.setIcon(icon)
            btn.clicked.connect(
                lambda checked, s=section_id: self.section_selected.emit(s)
            )
            self.buttons[section_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Footer con informazioni
        footer = QLabel("v1.0")
        footer.setStyleSheet("font-size: 8px; color: gray;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        self.setLayout(layout)
        self.setMaximumWidth(200)

    def highlight_section(self, section_id: str):
        """Evidenzia il pulsante della sezione selezionata"""
        for btn_id, btn in self.buttons.items():
            if btn_id == section_id:
                btn.setStyleSheet("font-weight: bold; border: 2px solid #0066CC;")
            else:
                btn.setStyleSheet("")


class VolleyballScoutApp(QMainWindow):
    """Main Application Window with integrated navigation"""

    def __init__(self):
        # Inizializza l'applicazione principale con navigazione integrata.
        super().__init__()
        self.setWindowTitle("🏐 Volleyball Scout")
        self.setGeometry(100, 100, 1600, 900)

        # Initialize Database
        try:
            self.db = DatabaseManager()
            print("✅ Database connesso")
        except Exception as e:
            print(f"❌ Errore connessione database: {e}")
            self.db = None

        # Main layout with navigation
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left: Navigation Menu
        self.nav_menu = NavigationMenu()
        self.nav_menu.section_selected.connect(self._on_section_selected)
        main_layout.addWidget(self.nav_menu)

        # Right: Content area with stacked widget
        self.content_stack = QStackedWidget()

        if self.db:
            # Crea tutte le sezioni
            self._setup_sections()
        else:
            # Mostra errore
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_layout.addWidget(
                QLabel("❌ Errore: Impossibile connettere il database")
            )
            error_widget.setLayout(error_layout)
            self.content_stack.addWidget(error_widget)

        main_layout.addWidget(self.content_stack, 1)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Mostra la dashboard per default
        self._on_section_selected("dashboard")

    def _setup_sections(self):
        """Setup di tutte le sezioni disponibili"""
        # 1. Dashboard
        self.dashboard = DashboardView(self.db)
        self.content_stack.addWidget(self.dashboard)

        # 2. Teams & Players Management
        if TeamManagementWidget:
            try:
                self.teams_widget = TeamManagementWidget(self.db)
                # Load teams data
                self.teams_widget.load_teams()
            except Exception as e:
                print(f"⚠️ Error creating TeamManagementWidget: {e}")
                self.teams_widget = PlaceholderWidget("👥 Squadre e Giocatori")
        else:
            self.teams_widget = PlaceholderWidget("👥 Squadre e Giocatori")
        self.content_stack.addWidget(self.teams_widget)

        # 3. Gestione incontri
        if RosterSetupWidget:
            self.roster_widget = RosterSetupWidget(self.db)
            if hasattr(self.roster_widget, "scout_resume_requested"):
                self.roster_widget.scout_resume_requested.connect(self._on_scout_ready)
            if hasattr(self.roster_widget, "match_deleted"):
                self.roster_widget.match_deleted.connect(self._on_match_deleted)
        else:
            self.roster_widget = PlaceholderWidget("🧾 Gestione incontri")
        self.content_stack.addWidget(self.roster_widget)

        # 4. Formation Setup Complete (with match selector)
        if FormationSetupComplete:
            try:
                self.formation_widget = FormationSetupComplete(self.db)
            except Exception as e:
                print(f"⚠️ Error loading FormationSetupComplete: {e}")
                self.formation_widget = PlaceholderWidget("🏐 Formazioni")
        else:
            self.formation_widget = PlaceholderWidget("🏐 Formazioni")
        self.content_stack.addWidget(self.formation_widget)

        # 5. Scout & Video
        scout_container = QWidget()
        scout_layout = QHBoxLayout()

        if ScoutPanel and self.db is not None:
            self.scout_panel = ScoutPanel(self.db)
            if hasattr(self.scout_panel, "set_finished"):
                self.scout_panel.set_finished.connect(self._on_set_finished)
            if hasattr(self.scout_panel, "back_requested"):
                self.scout_panel.back_requested.connect(self._on_back_to_scout_list)
            scout_layout.addWidget(self.scout_panel, 1)
        elif ScoutPanel:
            self.scout_panel = ScoutPanel()
            if hasattr(self.scout_panel, "back_requested"):
                self.scout_panel.back_requested.connect(self._on_back_to_scout_list)
            scout_layout.addWidget(self.scout_panel, 1)
        else:
            scout_layout.addWidget(QLabel("Scout Panel not available"), 1)

        if VideoPlayer:
            self.video_player = VideoPlayer()

            if hasattr(self, "scout_panel"):
                if hasattr(self.video_player, "source_changed") and hasattr(
                    self.scout_panel, "set_video_source"
                ):
                    self.video_player.source_changed.connect(
                        self.scout_panel.set_video_source
                    )
                if hasattr(self.video_player, "playback_position_changed") and hasattr(
                    self.scout_panel, "set_video_time"
                ):
                    self.video_player.playback_position_changed.connect(
                        self.scout_panel.set_video_time
                    )
                if hasattr(self.video_player, "playback_state_changed") and hasattr(
                    self.scout_panel, "set_video_playback_state"
                ):
                    self.video_player.playback_state_changed.connect(
                        self.scout_panel.set_video_playback_state
                    )

            embedded_in_panel = False
            if hasattr(self, "scout_panel") and hasattr(
                self.scout_panel, "set_video_widget"
            ):
                self.scout_panel.set_video_widget(self.video_player)
                embedded_in_panel = True

            if not embedded_in_panel:
                scout_layout.addWidget(self.video_player, 2)
        else:
            if not (
                hasattr(self, "scout_panel")
                and hasattr(self.scout_panel, "set_video_widget")
            ):
                scout_layout.addWidget(QLabel("Video Player not available"), 2)

        scout_container.setLayout(scout_layout)
        self.content_stack.addWidget(scout_container)

        # Collega il completamento formazione al passaggio in scouting live
        if hasattr(self, "formation_widget") and hasattr(
            self.formation_widget, "scout_ready"
        ):
            self.formation_widget.scout_ready.connect(self._on_scout_ready)

        # 6. Statistics
        if StatsView:
            self.stats_view = StatsView()
        else:
            self.stats_view = PlaceholderWidget("📈 Statistiche")
        self.content_stack.addWidget(self.stats_view)

    def _on_match_deleted(self, match_id: int):
        if hasattr(self, "formation_widget") and hasattr(
            self.formation_widget, "matches_widget"
        ):
            self.formation_widget.matches_widget._load_matches()
        if hasattr(self, "dashboard") and hasattr(self.dashboard, "refresh"):
            self.dashboard.refresh()

    def _on_section_selected(self, section_id: str):
        """Cambia la sezione visualizzata"""
        section_map = {
            "dashboard": 0,
            "teams": 1,
            "roster": 2,
            "formation": 3,
            "scout": 4,
            "stats": 5,
        }

        if section_id in section_map:
            self.content_stack.setCurrentIndex(section_map[section_id])
            self.nav_menu.highlight_section(section_id)

            # Refresh della dashboard quando viene visualizzata
            if section_id == "dashboard" and self.db:
                self.dashboard.refresh()

            # Refresh della formation quando viene visualizzata
            if section_id == "formation" and self.db:
                self._refresh_formation_panel()

    def _on_scout_ready(self, scout_payload: dict):
        """Quando la formazione è confermata, carica il contesto in Scouting Live e naviga."""
        resume_seconds = None
        if hasattr(self, "scout_panel") and hasattr(
            self.scout_panel, "load_match_context"
        ):
            self.scout_panel.load_match_context(scout_payload)
            if hasattr(self.scout_panel, "get_video_resume_seconds"):
                resume_seconds = self.scout_panel.get_video_resume_seconds()

        video_path = (
            scout_payload.get("video_path") if isinstance(scout_payload, dict) else None
        )
        if (
            video_path
            and hasattr(self, "video_player")
            and hasattr(self.video_player, "source_type")
            and hasattr(self.video_player, "source_input")
        ):
            file_idx = self.video_player.source_type.findData("file")
            if file_idx >= 0:
                self.video_player.source_type.setCurrentIndex(file_idx)
            self.video_player.source_input.setText(str(video_path))
            if hasattr(self.video_player, "connect_current_source"):
                self.video_player.connect_current_source()

        if (
            resume_seconds is not None
            and hasattr(self, "video_player")
            and hasattr(self.video_player, "set_resume_position")
        ):
            self.video_player.set_resume_position(resume_seconds)

        if hasattr(self, "scout_panel") and hasattr(
            self.scout_panel, "set_video_resume_badge"
        ):
            self.scout_panel.set_video_resume_badge(resume_seconds)

        self._on_section_selected("scout")

    def _on_set_finished(self, payload: dict):
        """Dopo Fine Set, torna alla formazione o chiude il match se concluso."""
        match_id = payload.get("match_id") if isinstance(payload, dict) else None
        next_set_number = (
            payload.get("next_set_number") if isinstance(payload, dict) else None
        )
        match_completed = (
            bool(payload.get("match_completed")) if isinstance(payload, dict) else False
        )

        self._on_section_selected("formation")

        if match_completed:
            if hasattr(self, "formation_widget") and hasattr(
                self.formation_widget, "stacked_widget"
            ):
                self.formation_widget.stacked_widget.setCurrentIndex(0)
            if hasattr(self, "formation_widget") and hasattr(
                self.formation_widget, "matches_widget"
            ):
                self.formation_widget.matches_widget._load_matches()

            return

        if (
            match_id is not None
            and next_set_number is not None
            and hasattr(self, "formation_widget")
            and hasattr(self.formation_widget, "open_match_by_id")
        ):
            opened = self.formation_widget.open_match_by_id(
                match_id,
                set_number=next_set_number,
            )
            if not opened:
                print(
                    f"⚠️ Impossibile aprire automaticamente la formation per match {match_id} (set {next_set_number})"
                )

    def _on_back_to_scout_list(self):
        """Ritorna alla lista match/formazioni dal pannello scouting live."""
        self._on_section_selected("formation")

        if hasattr(self, "formation_widget") and hasattr(
            self.formation_widget, "stacked_widget"
        ):
            self.formation_widget.stacked_widget.setCurrentIndex(0)

        if hasattr(self, "formation_widget") and hasattr(
            self.formation_widget, "matches_widget"
        ):
            self.formation_widget.matches_widget._load_matches()

    def _refresh_formation_panel(self):
        """Ricarica il FormationPanel con i dati attuali dal database"""
        try:
            # Load teams and players from database
            teams = []
            players_by_team = {}
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import Player, Team

                teams_data = session.query(Team).all()
                for team in teams_data:
                    teams.append({"id": team.id, "name": team.name})
                    players_data = (
                        session.query(Player).filter_by(team_id=team.id).all()
                    )
                    players_by_team[team.id] = [
                        {
                            "id": p.id,
                            "number": p.number,
                            "last_name": p.last_name,
                            "role": p.role,
                        }
                        for p in players_data
                    ]

            # Create formation panel with updated data
            if teams:
                new_widget = FormationPanel(teams, players_by_team)
            else:
                new_widget = PlaceholderWidget(
                    "🏐 Formazioni\n(Nessuna squadra nel database)"
                )

            # Sostituisci il widget nella stack
            old_widget = self.content_stack.widget(3)
            if old_widget:
                self.content_stack.removeWidget(old_widget)
                old_widget.deleteLater()

            self.formation_widget = new_widget
            self.content_stack.insertWidget(3, self.formation_widget)

        except Exception as e:
            print(f"⚠️ Error refreshing FormationPanel: {e}")

    def closeEvent(self, event):
        """Cleanup quando si chiude l'app"""
        if self.db:
            self.db.close()
        event.accept()


def main():
    """Avvia l'applicazione Volleyball Scout."""
    app = QApplication(sys.argv)

    # Use native system style (not Fusion)
    # This will use the default theme of the operating system
    # Don't set any specific style - let Qt use the native one

    window = VolleyballScoutApp()
    window.show()

    print("=" * 80)
    print("🏐 VOLLEYBALL SCOUT - PyQt6 Application")
    print("=" * 80)
    print("\n📋 Applicazione avviata!")
    print("   - Menu laterale con navigazione tra le sezioni")
    print("   - Dashboard: visualizza match e sessioni in bozza")
    print("   - Formazioni: seleziona titolari e libero")
    print("   - Scouting Live: inserisci eventi live")
    print("   - Statistiche: visualizza statistiche partita\n")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main() or 0)

"""
Volleyball Scout - Main PyQt6 Application with Dark Theme and Menu Bar
"""

import logging
import sys
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import UI components with error handling
try:
    from volleyball_scout.core.database import DatabaseManager
except ImportError:
    try:
        from core.database import DatabaseManager
    except ImportError as e:
        print(f"❌ Cannot import DatabaseManager: {e}")
        raise

try:
    from volleyball_scout.ui.team_management import TeamManagementWidget
except ImportError:
    try:
        from .team_management import TeamManagementWidget
    except ImportError as e:
        print(f"⚠️ Warning: TeamManagementWidget not available: {e}")
        TeamManagementWidget = None

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
    RosterSetupWidget = None

from volleyball_scout.ui.window_utils import clamp_window_to_screen

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

try:
    from volleyball_scout.ui.drafts.draft_widget import DraftListWidget
except ImportError:
    try:
        from .drafts.draft_widget import DraftListWidget
    except ImportError as e:
        print(f"⚠️ Warning: DraftListWidget not available: {e}")
        DraftListWidget = None

# Import assets module
try:
    from volleyball_scout.ui.assets import (
        get_icon,
        get_logo_icon,
        get_logo_pixmap,
        get_section_icon,
    )
except ImportError:
    try:
        from .assets import get_icon, get_logo_icon, get_logo_pixmap, get_section_icon
    except ImportError as e:
        print(f"⚠️ Warning: Assets module not available: {e}")
        get_logo_pixmap = None
        get_icon = None
        get_logo_icon = None
        get_section_icon = None


# DARK THEME STYLESHEET
DARK_STYLESHEET = """
QMainWindow, QWidget, QDialog {
    background-color: #2B211C;
    color: #F6EFE9;
}

QMenuBar {
    background-color: #3A2D27;
    color: #F6EFE9;
    border-bottom: 1px solid #6E4B32;
}

QMenuBar::item:selected {
    background-color: #6E4B32;
}

QMenu {
    background-color: #3A2D27;
    color: #F6EFE9;
    border: 1px solid #6E4B32;
}

QMenu::item:selected {
    background-color: #E95420;
    color: #ffffff;
}

QLabel, QCheckBox, QRadioButton {
    color: #F6EFE9;
}

QPushButton {
    background-color: #8A613F;
    color: white;
    border: 1px solid #6E4B32;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #A5784D;
}

QPushButton:pressed {
    background-color: #6E4B32;
}

QPushButton:disabled {
    background-color: #4F4035;
    color: #9D8878;
    border-color: #4F4035;
}

QTableWidget, QListWidget, QComboBox, QLineEdit, QTextEdit {
    background-color: #3A2D27;
    color: #F6EFE9;
    border: 1px solid #6E4B32;
    border-radius: 6px;
}

QTableWidget {
    alternate-background-color: #5A3D2A;
    gridline-color: #6E4B32;
}

QTableWidget::item {
    padding: 4px;
    border: none;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #E95420;
    color: white;
}

QHeaderView::section {
    background-color: #3A2D27;
    color: #F6EFE9;
    padding: 4px;
    border: 1px solid #6E4B32;
}

QScrollBar:vertical {
    background-color: #2B211C;
    width: 12px;
}

QScrollBar::handle:vertical {
    background-color: #8A613F;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #A5784D;
}

QStackedWidget {
    background-color: #2B211C;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QRadioButton::indicator:unchecked {
    background-color: #4F4035;
    border: 2px solid #7D6757;
    border-radius: 8px;
}

QRadioButton::indicator:checked {
    background-color: #E95420;
    border: 2px solid #E95420;
    border-radius: 8px;
}

QLineEdit, QTextEdit {
    padding: 6px;
    selection-background-color: #E95420;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid #E95420;
}

QGroupBox {
    border: 1px solid #6E4B32;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #E95420;
}
"""

# LIGHT THEME STYLESHEET
LIGHT_STYLESHEET = """
QMainWindow, QWidget, QDialog {
    background-color: #FFF7F2;
    color: #2B211C;
}

QMenuBar {
    background-color: #F6EAE4;
    color: #2B211C;
    border-bottom: 1px solid #D8B7AA;
}

QMenuBar::item:selected {
    background-color: #EDD7CE;
}

QMenu {
    background-color: #FFF7F2;
    color: #2B211C;
    border: 1px solid #D8B7AA;
}

QMenu::item:selected {
    background-color: #E95420;
    color: #ffffff;
}

QLabel, QCheckBox, QRadioButton {
    color: #2B211C;
}

QPushButton {
    background-color: #E95420;
    color: white;
    border: 1px solid #C7451A;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #F06B3C;
}

QPushButton:pressed {
    background-color: #C7451A;
}

QPushButton:disabled {
    background-color: #E6CDC2;
    color: #9D7E72;
    border-color: #D8B7AA;
}

QTableWidget, QListWidget, QComboBox, QLineEdit, QTextEdit {
    background-color: #FFFFFF;
    color: #2B211C;
    border: 1px solid #D8B7AA;
    border-radius: 6px;
}

QTableWidget {
    alternate-background-color: #FFF1EA;
    gridline-color: #E6CDC2;
}

QTableWidget::item {
    padding: 4px;
    border: none;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #E95420;
    color: white;
}

QHeaderView::section {
    background-color: #F6EAE4;
    color: #2B211C;
    padding: 4px;
    border: 1px solid #D8B7AA;
}

QScrollBar:vertical {
    background-color: #FFF7F2;
    width: 12px;
}

QScrollBar::handle:vertical {
    background-color: #D1B2A6;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #C39B8C;
}

QStackedWidget {
    background-color: #FFF7F2;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QRadioButton::indicator:unchecked {
    background-color: #FFFFFF;
    border: 2px solid #D8B7AA;
    border-radius: 8px;
}

QRadioButton::indicator:checked {
    background-color: #E95420;
    border: 2px solid #E95420;
    border-radius: 8px;
}

QLineEdit, QTextEdit {
    padding: 6px;
    selection-background-color: #E95420;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid #E95420;
}

QGroupBox {
    border: 1px solid #D8B7AA;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #C7451A;
}
"""


class LoginDialog(QDialog):
    """Dialog semplice per il login"""

    def __init__(self, parent=None):
        # Inizializza il dialogo di login con layout e credenziali predefinite.
        super().__init__(parent)
        self.setWindowTitle("Volleyball Scout - Login")
        self.setGeometry(400, 300, 400, 200)
        self.setModal(True)
        self.setStyleSheet(DARK_STYLESHEET)

        layout = QVBoxLayout()

        # Titolo
        title = QLabel("Volleyball Scout")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setText("admin")  # Default value
        self.username_input.setMinimumHeight(35)
        layout.addWidget(self.username_input)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setText("password")  # Default value
        self.password_input.setMinimumHeight(35)
        layout.addWidget(self.password_input)

        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Accedi")
        self.login_button.setMinimumHeight(40)
        self.login_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        )
        self.login_button.clicked.connect(self.accept)
        button_layout.addWidget(self.login_button)

        self.cancel_button = QPushButton("Annulla")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        )
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Permetti di inviare il form con Enter
        self.password_input.returnPressed.connect(self.accept)

    def get_credentials(self):
        """Ritorna le credenziali inserite"""
        return self.username_input.text(), self.password_input.text()


class PlaceholderWidget(QWidget):
    """Placeholder widget per sezioni non disponibili"""

    def __init__(self, title="Coming Soon", parent=None):
        # Inizializza il widget segnaposto con un titolo.
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addStretch()

        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        label.setFont(font)
        label.setStyleSheet("color: #9D8878;")

        layout.addWidget(label)
        layout.addStretch()
        self.setLayout(layout)


class DashboardView(QWidget):
    """Enhanced Dashboard widget with cards cliccabili e logo"""

    def __init__(self, db_manager, on_navigate=None, parent=None):
        # Inizializza la dashboard con griglia di carte e logo.
        super().__init__(parent)
        self.db = db_manager
        self.on_navigate = on_navigate
        self.is_dark_theme = True
        self.card_buttons = []

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Logo section at the top
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()

        if callable(get_logo_pixmap):
            try:
                logo_pixmap = get_logo_pixmap(80)
                logo_label = QLabel()
                logo_label.setPixmap(logo_pixmap)
                logo_layout.addWidget(logo_label)
            except Exception as e:
                print(f"⚠️ Could not load logo: {e}")

        logo_layout.addStretch()
        main_layout.addLayout(logo_layout)

        # Title
        title = QLabel("Volleyball Scout - Dashboard")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Benvenuto nella dashboard principale")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; margin-bottom: 20px;")
        self.subtitle_label = subtitle
        main_layout.addWidget(subtitle)

        # Cards Grid
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)

        # Define cards
        cards = [
            {
                "title": "Squadre e Giocatori",
                "description": "Gestisci squadre e giocatori",
                "section_id": "teams",
            },
            {
                "title": "Gestione incontri",
                "description": "Configura i giocatori convocati",
                "section_id": "roster",
            },
            {
                "title": "Scouting Live",
                "description": "Registra e analizza video",
                "section_id": "scout",
            },
            {
                "title": "Statistiche",
                "description": "Visualizza statistiche partite",
                "section_id": "stats",
            },
            {
                "title": "Dashboard",
                "description": "Aggiorna la schermata principale",
                "section_id": "dashboard",
            },
        ]

        for idx, card in enumerate(cards):
            card_widget = self._create_card_widget(
                card["title"], card["description"], card["section_id"]
            )
            cards_layout.addWidget(card_widget, idx // 3, idx % 3)

        main_layout.addLayout(cards_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)
        self.set_theme(True)

    def _card_stylesheet(self):
        # Restituisce il foglio di stile per le carte in base al tema.
        if self.is_dark_theme:
            return """
                QPushButton {
                    background-color: #3A2D27;
                    color: #F6EFE9;
                    border: 1px solid #6E4B32;
                    border-radius: 10px;
                    padding: 12px;
                    text-align: left;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5A3D2A;
                    border: 1px solid #E95420;
                }
                QPushButton:pressed {
                    background-color: #2B211C;
                    border: 1px solid #C7451A;
                }
            """

        return """
            QPushButton {
                background-color: #FFF1EA;
                color: #2B211C;
                border: 1px solid #D8B7AA;
                border-radius: 10px;
                padding: 12px;
                text-align: left;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FDE7DC;
                border: 1px solid #E95420;
            }
            QPushButton:pressed {
                background-color: #F8D8C8;
                border: 1px solid #C7451A;
            }
        """

    def set_theme(self, is_dark: bool):
        """Imposta il tema scuro o chiaro per la dashboard."""
        self.is_dark_theme = is_dark
        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setStyleSheet(
                (
                    "color: #C6B3A5; font-size: 12px; margin-bottom: 20px;"
                    if is_dark
                    else "color: #7D6757; font-size: 12px; margin-bottom: 20px;"
                )
            )

        card_css = self._card_stylesheet()
        for btn in self.card_buttons:
            btn.setStyleSheet(card_css)

    def _create_card_widget(
        self, title: str, description: str, section_id: str
    ) -> QWidget:
        """Create una card cliccabile per la dashboard"""
        card_btn = QPushButton(f"{title}\n{description}")
        card_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        card_btn.setMinimumHeight(110)

        if callable(get_section_icon):
            icon = get_section_icon(section_id, size=20)
            if not icon.isNull():
                card_btn.setIcon(icon)
                card_btn.setIconSize(QSize(22, 22))
        self.card_buttons.append(card_btn)

        navigate_fn = self.on_navigate
        if callable(navigate_fn):
            card_btn.clicked.connect(
                lambda checked, sid=section_id, fn=navigate_fn: fn(sid)
            )

        return card_btn

    def refresh(self):
        """Refresh dashboard data"""
        pass


class VolleyballScoutApp(QMainWindow):
    """Main Application Window"""

    def __init__(self):
        # Inizializza l'applicazione principale con menu e sezioni.
        super().__init__()
        self.setWindowTitle("Volleyball Scout")
        self.setGeometry(100, 100, 1400, 780)
        clamp_window_to_screen(self, fallback_width=1400, fallback_height=780)

        # Set window icon if available
        if callable(get_logo_icon):
            try:
                icon = get_logo_icon(32)
                self.setWindowIcon(icon)
            except Exception as e:
                print(f"⚠️ Could not set window icon: {e}")

        # Applica tema scuro di default
        app = QApplication.instance()
        if app:
            app.setStyle("Fusion")
            app.setStyleSheet(DARK_STYLESHEET)

        # Stato del tema (True = dark, False = light)
        self.is_dark_theme = True
        self.theme_actions = {}  # Salva i QAction per i menu

        # Initialize Database
        try:
            self.db = DatabaseManager()
            print("✅ Database connesso")
        except Exception as e:
            print(f"❌ Errore connessione database: {e}")
            self.db = None

        # Stato di autenticazione
        self.is_authenticated = False
        self.current_user = None

        # Main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content area con stacked widget
        self.content_stack = QStackedWidget()

        if self.db:
            self._setup_sections()
        else:
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_layout.addWidget(QLabel("Errore: Impossibile connettere il database"))
            error_widget.setLayout(error_layout)
            self.content_stack.addWidget(error_widget)

        main_layout.addWidget(self.content_stack, 1)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Crea menu bar (dopo setup del widget)
        self._create_menu_bar()

        # Esegui auto-login
        if self.db:
            self._perform_auto_login()
        else:
            self.showErrorDialog(
                "Errore",
                "Impossibile connettere il database. Controllare la configurazione.",
            )

    def _create_menu_bar(self):
        """Crea il menu bar in alto"""
        menubar = self.menuBar()

        # Menu File
        file_menu = menubar.addMenu("File")
        file_menu.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))

        action_import = QAction("Importa da DataVolley...", self)
        action_import.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        )
        action_import.triggered.connect(self._import_datavolley)
        file_menu.addAction(action_import)

        file_menu.addSeparator()

        action_exit = QAction("Esci", self)
        action_exit.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        )
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # Menu Sezioni
        view_menu = menubar.addMenu("Sezioni")
        view_menu.setIcon(
            get_section_icon("dashboard", size=16)
            if callable(get_section_icon)
            else self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        )

        action_dashboard = QAction("Dashboard", self)
        if callable(get_section_icon):
            action_dashboard.setIcon(get_section_icon("dashboard", size=18))
        action_dashboard.triggered.connect(lambda: self._show_section("dashboard"))
        view_menu.addAction(action_dashboard)

        action_teams = QAction("Squadre e Giocatori", self)
        if callable(get_section_icon):
            action_teams.setIcon(get_section_icon("teams", size=18))
        action_teams.triggered.connect(lambda: self._show_section("teams"))
        view_menu.addAction(action_teams)

        action_roster = QAction("Gestione incontri", self)
        if callable(get_section_icon):
            action_roster.setIcon(get_section_icon("roster", size=18))
        action_roster.triggered.connect(lambda: self._show_section("roster"))
        view_menu.addAction(action_roster)

        action_scout = QAction("Scouting Live", self)
        if callable(get_section_icon):
            action_scout.setIcon(get_section_icon("scout", size=18))
        action_scout.triggered.connect(lambda: self._show_section("scout"))
        view_menu.addAction(action_scout)

        action_stats = QAction("Statistiche", self)
        if callable(get_section_icon):
            action_stats.setIcon(get_section_icon("stats", size=18))
        action_stats.triggered.connect(lambda: self._show_section("stats"))
        view_menu.addAction(action_stats)

        # Menu Preferenze
        preferences_menu = menubar.addMenu("Preferenze")
        preferences_menu.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )

        # Submenu Tema
        theme_menu = preferences_menu.addMenu("Tema")
        theme_menu.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        )

        # Azione Modalità Scura
        action_dark_mode = QAction("Modalità Scura", self, checkable=True)
        action_dark_mode.setChecked(True)  # Default
        action_dark_mode.triggered.connect(lambda: self._toggle_theme(True))
        theme_menu.addAction(action_dark_mode)
        self.theme_actions["dark"] = action_dark_mode

        # Azione Modalità Chiara
        action_light_mode = QAction("Modalità Chiara", self, checkable=True)
        action_light_mode.setChecked(False)  # Default
        action_light_mode.triggered.connect(lambda: self._toggle_theme(False))
        theme_menu.addAction(action_light_mode)
        self.theme_actions["light"] = action_light_mode

        preferences_menu.addSeparator()

        action_scout_settings = QAction("Impostazioni Scouting...", self)
        action_scout_settings.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        action_scout_settings.triggered.connect(self._open_scout_settings)
        preferences_menu.addAction(action_scout_settings)

        preferences_menu.addSeparator()

        action_formation_editor = QAction("Gestione formazioni ricezione...", self)
        action_formation_editor.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        action_formation_editor.triggered.connect(self._open_formation_editor)
        preferences_menu.addAction(action_formation_editor)

        # Menu Aiuto
        help_menu = menubar.addMenu("Aiuto")
        help_menu.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton)
        )

        action_about = QAction("About", self)
        action_about.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        )
        action_about.triggered.connect(self._show_about)
        help_menu.addAction(action_about)

        help_menu.addSeparator()

        action_code_legend = QAction("Legenda codici DataVolley", self)
        action_code_legend.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        action_code_legend.triggered.connect(self._show_code_legend)
        help_menu.addAction(action_code_legend)

    def _show_code_legend(self):
        from .dv_code_legend import DvSkillTable
        dialog = QDialog(self)
        dialog.setWindowTitle("Legenda Codici DataVolley")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        layout.addWidget(DvSkillTable(dialog))
        dialog.exec()

    def _import_datavolley(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from volleyball_scout.importers.datavolley_importer import DataVolleyImporter

        path, _ = QFileDialog.getOpenFileName(
            self, "Importa da DataVolley", "",
            "File DataVolley (*.dvw);;Tutti i file (*)",
        )
        if not path:
            return
        try:
            session = self.db.get_session()
            importer = DataVolleyImporter(session)
            result = importer.import_file(path)
            session.close()
            if result.get("duplicate"):
                QMessageBox.information(
                    self, "Import ignorato",
                    f"Partita {result['home_team']} vs {result['away_team']} già importata.",
                )
            else:
                QMessageBox.information(
                    self, "Import completato",
                    f"Partita importata: {result['home_team']} vs {result['away_team']}",
                )
                self._refresh_matches_list()
                self._show_section("roster")
        except Exception as e:
            logger.exception("Errore import DataVolley")
            QMessageBox.critical(self, "Errore import", str(e))

    def _refresh_matches_list(self):
        if hasattr(self, "dashboard") and hasattr(self.dashboard, "refresh"):
            self.dashboard.refresh()

    def _on_match_deleted(self, match_id: int):
        self._refresh_matches_list()

    def _setup_sections(self):
        """Setup di tutte le sezioni disponibili"""
        # 1. Dashboard
        if self.db is not None:
            self.dashboard = DashboardView(self.db, on_navigate=self._show_section)
            if hasattr(self.dashboard, "set_theme"):
                self.dashboard.set_theme(self.is_dark_theme)
        else:
            self.dashboard = PlaceholderWidget("Dashboard")
        self.content_stack.addWidget(self.dashboard)

        # 2. Teams & Players Management
        if TeamManagementWidget and self.db is not None:
            try:
                self.teams_widget = TeamManagementWidget(self.db)
                self.teams_widget.load_teams()
            except Exception as e:
                print(f"⚠️ Error creating TeamManagementWidget: {e}")
                self.teams_widget = PlaceholderWidget("Squadre e Giocatori")
        else:
            self.teams_widget = PlaceholderWidget("Squadre e Giocatori")
        self.content_stack.addWidget(self.teams_widget)

        # 3. Gestione incontri
        if RosterSetupWidget and self.db is not None:
            self.roster_widget = RosterSetupWidget(self.db)
            if hasattr(self.roster_widget, "roster_completed"):
                self.roster_widget.roster_completed.connect(
                    self._on_roster_setup_completed
                )
            if hasattr(self.roster_widget, "scout_resume_requested"):
                self.roster_widget.scout_resume_requested.connect(self._on_scout_ready)
            if hasattr(self.roster_widget, "match_deleted"):
                self.roster_widget.match_deleted.connect(self._on_match_deleted)
        else:
            self.roster_widget = PlaceholderWidget("Gestione incontri")
        self.content_stack.addWidget(self.roster_widget)

        # 4. Scout & Video
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

        # 5. Statistics
        if StatsView:
            self.stats_view = StatsView()
        else:
            self.stats_view = PlaceholderWidget("Statistics")
        self.content_stack.addWidget(self.stats_view)

    def _show_section(self, section_id: str):
        """Mostra una sezione specifica."""
        section_map = {
            "dashboard": 0,
            "teams": 1,
            "roster": 2,
            "scout": 3,
            "stats": 4,
        }

        if section_id in section_map:
            self.content_stack.setCurrentIndex(section_map[section_id])

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

            # Imposta il seek PRIMA di connettere la sorgente
            if resume_seconds is not None and hasattr(self.video_player, "set_resume_position"):
                self.video_player.set_resume_position(resume_seconds)

            if hasattr(self.video_player, "connect_current_source"):
                self.video_player.connect_current_source()

            # Ferma subito la riproduzione automatica
            if hasattr(self.video_player, "toggle_pause"):
                self.video_player.toggle_pause()

        if (
            resume_seconds is not None
            and hasattr(self, "video_player")
            and hasattr(self.video_player, "set_resume_position")
        ):
            # Fallback: se il video non era presente, cerca comunque di impostare il resume
            if not video_path:
                self.video_player.set_resume_position(resume_seconds)

        if hasattr(self, "scout_panel") and hasattr(
            self.scout_panel, "set_video_resume_badge"
        ):
            self.scout_panel.set_video_resume_badge(resume_seconds)

        self._show_section("scout")

    def _on_set_finished(self, payload: dict):
        """Dopo Fine Set, torna alla gestione incontri o chiude il match se concluso."""
        match_completed = (
            bool(payload.get("match_completed")) if isinstance(payload, dict) else False
        )

        self._show_section("roster")

        if match_completed:
            if hasattr(self, "roster_widget") and hasattr(self.roster_widget, "refresh_matches"):
                self.roster_widget.refresh_matches()
            return

        if hasattr(self, "roster_widget") and hasattr(self.roster_widget, "refresh_matches"):
            self.roster_widget.refresh_matches()

    def _on_back_to_scout_list(self):
        """Ritorna alla lista match dal pannello scouting live."""
        self._show_section("roster")

        if hasattr(self, "roster_widget") and hasattr(self.roster_widget, "refresh_matches"):
            self.roster_widget.refresh_matches()

    def _on_roster_setup_completed(self):
        """Dopo il roster completo, torna alla gestione incontri."""
        match_id = None

        if hasattr(self, "roster_widget"):
            current_match = getattr(self.roster_widget, "current_match", None)
            if isinstance(current_match, dict):
                match_id = current_match.get("id")

        # Torna alla gestione incontri
        self._show_section("roster")

        if hasattr(self, "roster_widget") and hasattr(self.roster_widget, "refresh_matches"):
            self.roster_widget.refresh_matches()

    def _open_scout_settings(self):
        # Apre il dialogo delle impostazioni di scouting.
        if hasattr(self, "scout_panel") and hasattr(
            self.scout_panel, "open_settings_dialog"
        ):
            self.scout_panel.open_settings_dialog()
            return

        QMessageBox.information(
            self,
            "Impostazioni Scouting",
            "Pannello scouting non disponibile.",
        )

    def _open_formation_editor(self):
        # Apre l'editor delle formazioni di ricezione.
        if hasattr(self, "scout_panel"):
            self.scout_panel._configure_rx_formation()
        else:
            QMessageBox.information(
                self,
                "Formazioni ricezione",
                "Apri prima lo Scouting Live per gestire le formazioni.",
            )

    def _toggle_theme(self, is_dark: bool):
        """Cambia il tema dell'applicazione"""
        self.is_dark_theme = is_dark
        app = QApplication.instance()

        if is_dark:
            # Applica tema scuro
            app.setStyleSheet(DARK_STYLESHEET)
            print("Tema scuro attivato")
        else:
            # Applica tema chiaro
            app.setStyleSheet(LIGHT_STYLESHEET)
            print("Tema chiaro attivato")

        # Aggiorna widget con temi personalizzati
        if hasattr(self, "dashboard") and hasattr(self.dashboard, "set_theme"):
            self.dashboard.set_theme(is_dark)

        # Aggiorna i checkmark dei menu items
        self.theme_actions["dark"].setChecked(is_dark)
        self.theme_actions["light"].setChecked(not is_dark)

    def _show_about(self):
        """Mostra finestra About"""
        QMessageBox.information(
            self,
            "About Volleyball Scout",
            "Volleyball Scout v1.0\n\n"
            "Applicazione per la scout e l'analisi di partite di pallavolo.\n\n"
            f"Utente: {self.current_user}\n\n"
            "© 2024",
        )

    def _perform_auto_login(self):
        """Esegui auto-login all'avvio"""
        print("🔐 Auto-login in corso...")

        # Credenziali hardcoded per la prototipazione
        username = "admin"
        password = "password"

        # Verifica credenziali (simulato - in produzione verificare con il DB)
        if self._verify_credentials(username, password):
            self.is_authenticated = True
            self.current_user = username
            print(f"✅ Auto-login riuscito per utente: {username}")
            # Mostra dashboard
            self._show_section("dashboard")
        else:
            # Se l'auto-login fallisce, mostra il dialog di login
            print("⚠️ Auto-login fallito, mostra dialog di login")
            self._show_login_dialog()

    def _show_login_dialog(self):
        """Mostra il dialog di login"""
        while not self.is_authenticated:
            dialog = LoginDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                username, password = dialog.get_credentials()

                if self._verify_credentials(username, password):
                    self.is_authenticated = True
                    self.current_user = username
                    print(f"✅ Login riuscito per utente: {username}")
                    self._show_section("dashboard")
                    break
                else:
                    # Login fallito
                    self.showErrorDialog(
                        "Login Fallito",
                        "Credenziali non valide. Riprova.",
                    )
            else:
                # Utente ha annullato il login
                self.close()
                break

    def _verify_credentials(self, username: str, password: str) -> bool:
        """Verifica le credenziali"""
        # Implementazione semplice per prototipazione
        # In produzione, verificare con il database
        valid_users = {
            "admin": "password",
            "coach": "coach123",
            "scout": "scout123",
        }
        return valid_users.get(username) == password

    def _perform_logout(self):
        """Esegui logout e torna al login"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Sei sicuro di voler fare logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.is_authenticated = False
            self.current_user = None
            print("Logout eseguito")
            self._show_login_dialog()

    def showErrorDialog(self, title: str, message: str):
        """Mostra un dialog di errore"""
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event):
        """Cleanup quando si chiude l'app"""
        close_fn = getattr(self.db, "close", None)
        if callable(close_fn):
            close_fn()
        event.accept()


def main():
    """Avvia l'applicazione Volleyball Scout."""
    import argparse
    parser = argparse.ArgumentParser(description="Volleyball Scout")
    parser.add_argument("--debug", action="store_true", help="Abilita log di debug")
    args, _ = parser.parse_known_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging attivato")

    app = QApplication(sys.argv)

    window = VolleyballScoutApp()
    window.show()

    print("=" * 80)
    print("🏐 VOLLEYBALL SCOUT - PyQt6 Application")
    print("=" * 80)
    print("\n📋 Applicazione avviata!")
    print("   - Menu in alto per navigare le sezioni")
    print("   - File → Esci per chiudere l'applicazione")
    print("   - Tema scuro attivato")
    print("   - Assets caricati\n")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main() or 0)

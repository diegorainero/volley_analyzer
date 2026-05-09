#!/usr/bin/env python3
"""
Demo interattivo del Light/Dark Theme Toggle
Questo script mostra come funziona il toggle tema senza avviare l'app completa.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

try:
    from volleyball_scout.ui.app_dark import DARK_STYLESHEET, LIGHT_STYLESHEET
except ImportError:
    # Fallback if import fails
    DARK_STYLESHEET = ""
    LIGHT_STYLESHEET = ""
    print("⚠️ Warning: Stylesheet not imported")


class ThemeToggleDemoApp(QMainWindow):
    """Demo app per il toggle tema"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 Light/Dark Theme Toggle Demo")
        self.setGeometry(100, 100, 600, 400)

        # Stato tema
        self.is_dark_theme = True
        self.theme_actions = {}

        # Widget centrale
        widget = QWidget()
        layout = QVBoxLayout()

        # Titolo
        title = QLabel("🎨 Theme Toggle Demo")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Sottotitolo
        subtitle = QLabel("Usa il menu ⚙️ Preferenze → 🎨 Tema per cambiare tema")
        layout.addWidget(subtitle)

        # Informazione stato
        self.status_label = QLabel("Tema attivo: 🌙 Scuro")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Info stylesheet
        layout.addWidget(QLabel(f"\n📊 Statistiche Stylesheet:"))
        layout.addWidget(QLabel(f"  Dark: {len(DARK_STYLESHEET)} caracteres"))
        layout.addWidget(QLabel(f"  Light: {len(LIGHT_STYLESHEET)} caracteres"))

        # Pulsante toggle manuale
        toggle_btn = QPushButton("🔄 Toggle Tema")
        toggle_btn.clicked.connect(self._manual_toggle)
        layout.addWidget(toggle_btn)

        layout.addStretch()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Applica tema scuro iniziale
        app = QApplication.instance()
        if app:
            app.setStyle("Fusion")
            app.setStyleSheet(DARK_STYLESHEET)

        # Menu bar
        self._create_menu_bar()

    def _create_menu_bar(self):
        """Crea menu bar con tema toggle"""
        menubar = self.menuBar()

        # Menu Preferenze
        pref_menu = menubar.addMenu("⚙️ Preferenze")

        # Submenu Tema
        theme_menu = pref_menu.addMenu("🎨 Tema")

        # Dark mode action
        dark_action = QAction("🌙 Modalità Scura", self, checkable=True)
        dark_action.setChecked(True)
        dark_action.triggered.connect(lambda: self._toggle_theme(True))
        theme_menu.addAction(dark_action)
        self.theme_actions["dark"] = dark_action

        # Light mode action
        light_action = QAction("☀️ Modalità Chiara", self, checkable=True)
        light_action.setChecked(False)
        light_action.triggered.connect(lambda: self._toggle_theme(False))
        theme_menu.addAction(light_action)
        self.theme_actions["light"] = light_action

        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _toggle_theme(self, is_dark: bool):
        """Toggle tra tema scuro e chiaro"""
        self.is_dark_theme = is_dark
        app = QApplication.instance()

        if is_dark:
            app.setStyleSheet(DARK_STYLESHEET)
            self.status_label.setText("Tema attivo: 🌙 Scuro")
            print("🌙 Tema scuro attivato")
        else:
            app.setStyleSheet(LIGHT_STYLESHEET)
            self.status_label.setText("Tema attivo: ☀️ Chiaro")
            print("☀️ Tema chiaro attivato")

        # Aggiorna checkmark
        self.theme_actions["dark"].setChecked(is_dark)
        self.theme_actions["light"].setChecked(not is_dark)

    def _manual_toggle(self):
        """Toggle manuale tramite pulsante"""
        self._toggle_theme(not self.is_dark_theme)

    def _show_about(self):
        """Mostra finestra about"""
        print("\n📋 Theme Toggle Demo v1.0")
        print("Questo è un demo del sistema di toggle tema.")
        print("✨ Click su ⚙️ Preferenze → 🎨 Tema per provare!")


def main():
    """Main function"""
    app = QApplication(sys.argv)
    window = ThemeToggleDemoApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

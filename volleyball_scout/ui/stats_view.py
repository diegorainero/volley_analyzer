import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)


class StatsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("Statistiche")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; "
            "border: 1px solid #B79C8A; border-radius: 8px; padding: 8px;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Dashboard statistiche (placeholder)")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 11px;")
        layout.addWidget(subtitle)

        # Pulsante per applicare la migrazione Alembic
        self.mig_btn = QPushButton("Applica Migrazione DB (Alembic)")
        self.mig_btn.setMinimumHeight(46)
        self.mig_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.mig_btn.clicked.connect(self.run_migration)
        self.mig_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #E95420;
                color: white;
                border: 1px solid #C7451A;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #F06B3C;
            }
            QPushButton:pressed {
                background-color: #C7451A;
            }
            """
        )
        layout.addWidget(self.mig_btn)

        layout.addStretch()

    def run_migration(self):
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../")
        )
        alembic_cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
        try:
            subprocess.run(
                alembic_cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            QMessageBox.information(
                self, "Migrazione completata", "Migrazione applicata con successo."
            )
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Errore migrazione", f"Errore:\n{e.stderr}")

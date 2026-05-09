import os
import subprocess
import sys

from PyQt6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget


class StatsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Stats View - Dashboard statistiche (placeholder)"))

        # Pulsante per applicare la migrazione Alembic
        self.mig_btn = QPushButton("Applica Migrazione DB (Alembic)")
        self.mig_btn.clicked.connect(self.run_migration)
        layout.addWidget(self.mig_btn)

        self.setLayout(layout)

    def run_migration(self):
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../")
        )
        alembic_cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
        try:
            result = subprocess.run(
                alembic_cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            QMessageBox.information(
                self, "Migrazione completata", "Migrazione applicata con successo!"
            )
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Errore migrazione", f"Errore:\n{e.stderr}")

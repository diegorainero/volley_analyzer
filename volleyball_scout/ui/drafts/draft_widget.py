"""
DraftListWidget - Widget per visualizzare e gestire le sessioni in bozza
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
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

from volleyball_scout.core.database import DatabaseManager

from .draft_manager import DraftManager


class DraftListWidget(QWidget):
    """Widget per visualizzare la lista di sessioni in bozza"""

    draft_resumed = pyqtSignal(int)  # match_id
    draft_deleted = pyqtSignal(int)  # match_id

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.draft_manager = DraftManager(db_manager)

        self.init_ui()
        self.load_drafts()

    def init_ui(self):
        """Inizializza l'interfaccia"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Titolo
        title = QLabel("📝 Sessioni in Bozza")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Descrizione
        desc = QLabel(
            "Le sessioni in bozza vengono salvate automaticamente. "
            "Clicca su una per riprendere da dove hai lasciato."
        )
        desc.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(desc)

        # Lista drafts
        self.drafts_list = QListWidget()
        self.drafts_list.itemClicked.connect(self._on_draft_clicked)
        layout.addWidget(self.drafts_list)

        # Bottoni di controllo
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_resume = QPushButton("▶ Riprendi")
        self.btn_resume.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_resume.clicked.connect(self._on_resume_clicked)
        self.btn_resume.setEnabled(False)
        buttons_layout.addWidget(self.btn_resume)

        self.btn_delete = QPushButton("🗑 Elimina")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.btn_delete.setEnabled(False)
        buttons_layout.addWidget(self.btn_delete)

        layout.addLayout(buttons_layout)

        # Empty state
        self.empty_state = QLabel(
            "Nessuna sessione in bozza.\nClicca su 'Nuovo Incontro' per iniziare!"
        )
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setStyleSheet("color: #999; font-style: italic; margin: 20px;")
        layout.addWidget(self.empty_state)
        self.empty_state.hide()

        self.setLayout(layout)

    def load_drafts(self):
        """Carica la lista di bozze dal database"""
        self.drafts_list.clear()

        drafts = self.draft_manager.get_drafts()

        if not drafts:
            self.empty_state.show()
            self.drafts_list.hide()
            return
        else:
            self.empty_state.hide()
            self.drafts_list.show()

        for draft in drafts:
            event_count = self.draft_manager.get_draft_event_count(draft["id"])

            # Formatta la data
            date_str = (
                draft["date"].strftime("%d/%m/%Y %H:%M")
                if draft["date"]
                else "Data sconosciuta"
            )
            updated_str = (
                draft["updated_at"].strftime("%d/%m/%Y %H:%M")
                if draft["updated_at"]
                else "Unknown"
            )

            # Crea il testo dell'item
            text = (
                f"{'▶️ ' if event_count > 0 else '📝 '}"
                f"{draft['home_team_name']} vs {draft['away_team_name']}\n"
                f"   Data: {date_str} | Ultimi eventi: {event_count} | Modificato: {updated_str}"
            )

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, draft["id"])

            # Colora in base allo stato
            if event_count > 0:
                item.setForeground(QColor("#27ae60"))  # Verde se ha eventi

            self.drafts_list.addItem(item)

    def _on_draft_clicked(self, item: QListWidgetItem):
        """Gestisce il click su una bozza"""
        self.btn_resume.setEnabled(True)
        self.btn_delete.setEnabled(True)

    def _on_resume_clicked(self):
        """Riprende la bozza selezionata"""
        item = self.drafts_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Avviso", "Seleziona una bozza da riprendere")
            return

        match_id = item.data(Qt.ItemDataRole.UserRole)
        if match_id is None:
            return

        # Cambia lo status da draft a in_progress
        if self.draft_manager.resume_draft(match_id):
            self.draft_resumed.emit(match_id)
            self.load_drafts()  # Ricarica la lista
        else:
            QMessageBox.critical(self, "Errore", "Impossibile riprendere la bozza")

    def _on_delete_clicked(self):
        """Elimina la bozza selezionata"""
        item = self.drafts_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Avviso", "Seleziona una bozza da eliminare")
            return

        match_id = item.data(Qt.ItemDataRole.UserRole)
        if match_id is None:
            return

        # Conferma l'eliminazione
        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            "Sei sicuro di voler eliminare questa bozza?\nL'azione non può essere annullata.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.draft_manager.delete_draft(match_id):
                self.draft_deleted.emit(match_id)
                self.load_drafts()  # Ricarica la lista
                QMessageBox.information(
                    self, "Successo", "Bozza eliminata correttamente"
                )
            else:
                QMessageBox.critical(self, "Errore", "Impossibile eliminare la bozza")

from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ScoutPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Scout Panel - Tastiera eventi live"))
        # Placeholder: aggiungi qui i pulsanti per le skill/eventi
        layout.addWidget(QPushButton("Attacco"))
        layout.addWidget(QPushButton("Muro"))
        layout.addWidget(QPushButton("Battuta"))
        layout.addWidget(QPushButton("Ricezione"))
        layout.addWidget(QPushButton("Alzata"))
        layout.addWidget(QPushButton("Difesa"))
        self.setLayout(layout)

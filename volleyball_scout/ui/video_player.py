from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Video Player (VLC) - Placeholder"))
        # Placeholder: aggiungi qui i controlli video
        layout.addWidget(QPushButton("Play"))
        layout.addWidget(QPushButton("Pausa"))
        layout.addWidget(QPushButton("Stop"))
        self.setLayout(layout)

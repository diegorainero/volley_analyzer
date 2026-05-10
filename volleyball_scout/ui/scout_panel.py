from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)


class ScoutPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Scouting Live")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; "
            "border: 1px solid #B79C8A; border-radius: 8px; padding: 8px;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Tastiera eventi live")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 11px;")
        layout.addWidget(subtitle)

        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(8)

        skills = [
            ("Attacco", QStyle.StandardPixmap.SP_MediaPlay),
            ("Muro", QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("Battuta", QStyle.StandardPixmap.SP_BrowserReload),
            ("Ricezione", QStyle.StandardPixmap.SP_DialogOpenButton),
            ("Alzata", QStyle.StandardPixmap.SP_ArrowForward),
            ("Difesa", QStyle.StandardPixmap.SP_ArrowBack),
        ]

        for idx, (label, icon_type) in enumerate(skills):
            btn = QPushButton(label)
            btn.setMinimumHeight(48)
            btn.setIcon(self.style().standardIcon(icon_type))
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #8A613F;
                    color: white;
                    border: 1px solid #6E4B32;
                    border-radius: 6px;
                    font-weight: bold;
                    text-align: left;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #A5784D;
                }
                QPushButton:pressed {
                    background-color: #6E4B32;
                }
                """
            )
            buttons_grid.addWidget(btn, idx // 2, idx % 2)

        layout.addLayout(buttons_grid)
        layout.addStretch()

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPoint
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QBrush,
    QFontDatabase,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QStyle,
)


class SidebarButton(QToolButton):
    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        self._icon_text = icon_text or text[:2].upper()
        self._hovered = False
        self._active = False
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setText(text)
        self.setMinimumSize(52, 52)
        self.setMaximumSize(60, 60)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

    def set_active(self, active: bool):
        self._active = active
        self.setChecked(active)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self.rect()
        is_down = self.isChecked() or self.isDown()

        # Background
        if is_down:
            bg = QColor("#1D6CFF")
        elif self._hovered:
            bg = QColor("#3A2D27")
        else:
            bg = QColor("transparent")

        if is_down:
            p.setBrush(QBrush(bg))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(r.adjusted(4, 2, -4, -2), 8, 8)
        elif self._hovered:
            p.setBrush(QBrush(bg))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(r.adjusted(4, 2, -4, -2), 8, 8)

        # Icon circle
        cx, cy = r.center().x(), 22
        radius = 14
        if is_down:
            p.setBrush(QBrush(QColor("#FFFFFF")))
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QBrush(QColor("#5A4A3E")))
            p.setPen(QPen(QColor("#8A7565"), 1))
        p.drawEllipse(QPoint(cx, cy), radius, radius)

        # Icon text
        f = QFont("Segoe UI", 9, QFont.Weight.Bold)
        p.setFont(f)
        if is_down:
            p.setPen(QColor("#1D6CFF"))
        else:
            p.setPen(QColor("#F6EFE9"))
        p.drawText(QRect(cx - radius, cy - radius, radius * 2, radius * 2),
                   Qt.AlignmentFlag.AlignCenter, self._icon_text)

        # Label text
        f2 = QFont("Segoe UI", 7)
        p.setFont(f2)
        if is_down:
            p.setPen(QColor("#FFFFFF"))
        elif self._hovered:
            p.setPen(QColor("#F6EFE9"))
        else:
            p.setPen(QColor("#B8A898"))
        p.drawText(QRect(0, cy + radius + 4, r.width(), 18),
                   Qt.AlignmentFlag.AlignCenter, self.text())

        p.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)


class SidebarToolbar(QWidget):
    section_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: dict[str, SidebarButton] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(60)
        self.setStyleSheet("""
            SidebarToolbar {
                background-color: #2B211C;
                border-right: 1px solid #4A382E;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 12, 4, 12)
        layout.setSpacing(2)

        sections = [
            ("dashboard", "DS", "Dashboard"),
            ("teams", "TM", "Squadre"),
            ("roster", "RS", "Roster"),
            ("scout", "SC", "Scout"),
            ("stats", "ST", "Stats"),
        ]

        for section_id, icon_text, label in sections:
            btn = SidebarButton(label, icon_text)
            btn.clicked.connect(lambda checked, sid=section_id: self._on_click(sid))
            self._buttons[section_id] = btn
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        # Settings button at bottom
        settings_btn = SidebarButton("Impostazioni", "SP")
        settings_btn.clicked.connect(lambda: self._on_click("settings"))
        self._buttons["settings"] = settings_btn
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_click(self, section_id: str):
        for sid, btn in self._buttons.items():
            btn.set_active(sid == section_id)
        self.section_changed.emit(section_id)

    def set_active_section(self, section_id: str):
        for sid, btn in self._buttons.items():
            btn.set_active(sid == section_id)

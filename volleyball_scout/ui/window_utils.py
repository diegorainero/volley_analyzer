from __future__ import annotations

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QWidget


def clamp_window_to_screen(window: QWidget, fallback_width: int = 1200, fallback_height: int = 800):
    screens = QGuiApplication.screens()
    if not screens:
        return

    target_screen = None
    win_pos = window.pos()
    for s in screens:
        geo = s.geometry()
        if geo.contains(win_pos):
            target_screen = s
            break
    if target_screen is None:
        target_screen = screens[0]

    screen_geo = target_screen.availableGeometry()
    max_w = screen_geo.width()
    max_h = screen_geo.height()

    cur_geo = window.geometry()
    new_w = min(cur_geo.width(), max_w, fallback_width)
    new_h = min(cur_geo.height(), max_h, fallback_height)

    # Ensure window is at most 85% of portrait/small-screen height
    max_reasonable_h = int(max_h * 0.85)
    if new_h > max_reasonable_h:
        new_h = max_reasonable_h

    new_x = max(screen_geo.x(), min(cur_geo.x(), screen_geo.x() + max_w - new_w))
    new_y = max(screen_geo.y(), min(cur_geo.y(), screen_geo.y() + max_h - new_h))

    window.setGeometry(new_x, new_y, new_w, new_h)



def clamp_window_size_to_screen(window: QWidget, fallback_w: int = 1400, fallback_h: int = 780):
    """Like clamp_window_to_screen but only clamps width/height, not position."""
    screens = QGuiApplication.screens()
    if not screens:
        return
    target_screen = screens[0]
    win_pos = window.pos()
    for s in screens:
        if s.geometry().contains(win_pos):
            target_screen = s
            break
    screen_geo = target_screen.availableGeometry()
    max_w = screen_geo.width()
    max_h = screen_geo.height()
    new_w = min(window.width(), max_w, fallback_w)
    new_h = min(window.height(), max_h, fallback_h, int(max_h * 0.85))
    window.resize(new_w, new_h)

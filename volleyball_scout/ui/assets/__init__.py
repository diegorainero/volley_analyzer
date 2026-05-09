"""
Assets module for Volleyball Scout UI
Provides utilities for loading icons and logos
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPixmap

ASSETS_DIR = Path(__file__).parent


def get_logo_pixmap(size: int = 100) -> QPixmap:
    """
    Load the main Volleyball Scout logo as a pixmap

    Args:
        size: Size in pixels (square)

    Returns:
        QPixmap of the logo, or a placeholder if not found
    """
    logo_path = ASSETS_DIR / "logo.svg"

    if logo_path.exists():
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(
                size, Qt.TransformationMode.SmoothTransformation
            )
            return pixmap

    # Fallback: create a simple placeholder
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor("#1e1e1e"))
    return pixmap


def get_icon(icon_name: str) -> QIcon:
    """
    Load an icon from the icons.svg file

    Args:
        icon_name: Name of the icon (e.g., 'dashboard', 'team', 'formation', 'scout', 'stats')

    Returns:
        QIcon of the specified icon
    """
    icons_path = ASSETS_DIR / "icons.svg"

    if not icons_path.exists():
        return QIcon()

    # Map icon names to their viewBox regions in the sprite
    icon_map = {
        "dashboard": (0, 0, 130, 160),
        "team": (150, 0, 130, 160),
        "formation": (290, 0, 130, 160),
        "scout": (430, 0, 130, 160),
        "stats": (570, 0, 130, 160),
    }

    if icon_name not in icon_map:
        return QIcon()

    # Create pixmap from SVG
    pixmap = QPixmap(str(icons_path))

    if not pixmap.isNull():
        # Simplification: return the full icons sprite
        # For production, you might want to crop individual icons
        pixmap = pixmap.scaledToHeight(24, Qt.TransformationMode.SmoothTransformation)
        return QIcon(pixmap)

    return QIcon()


def get_logo_icon(size: int = 32) -> QIcon:
    """
    Load the main logo as an icon

    Args:
        size: Size in pixels

    Returns:
        QIcon of the logo
    """
    pixmap = get_logo_pixmap(size)
    return QIcon(pixmap)

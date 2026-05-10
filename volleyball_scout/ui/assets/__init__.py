"""
Assets module for Volleyball Scout UI
Provides utilities for loading icons and logos
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPixmap

ASSETS_DIR = Path(__file__).parent
SECTIONS_DIR = ASSETS_DIR / "sections"
ROLES_DIR = ASSETS_DIR / "roles"

SECTION_ICON_FILES = {
    "dashboard": "dashboard.svg",
    "teams": "teams.svg",
    "roster": "roster.svg",
    "formation": "formation.svg",
    "scout": "scout.svg",
    "stats": "stats.svg",
}

ROLE_ICON_FILES = {
    "palleggiatore": "palleggiatore.svg",
    "opposto": "opposto.svg",
    "schiacciatore": "schiacciatore.svg",
    "banda": "schiacciatore.svg",
    "centrale": "centrale.svg",
    "libero": "libero.svg",
    "universale": "universale.svg",
    "capitano": "capitano.svg",
}


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


def _icon_from_svg_path(icon_path: Path, size: int = 20) -> QIcon:
    """Carica una icona SVG locale e la ridimensiona."""
    if not icon_path.exists():
        return QIcon()

    pixmap = QPixmap(str(icon_path))
    if pixmap.isNull():
        return QIcon(str(icon_path))

    scaled = pixmap.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return QIcon(scaled)


def get_section_icon(section_name: str, size: int = 20) -> QIcon:
    """Restituisce l'icona web della sezione richiesta."""
    file_name = SECTION_ICON_FILES.get(section_name)
    if not file_name:
        return QIcon()
    return _icon_from_svg_path(SECTIONS_DIR / file_name, size=size)


def get_role_icon(role_name: str, size: int = 16) -> QIcon:
    """Restituisce l'icona web associata al ruolo del giocatore."""
    if not role_name:
        return QIcon()

    key = role_name.strip().lower()
    file_name = ROLE_ICON_FILES.get(key)
    if not file_name:
        return QIcon()

    return _icon_from_svg_path(ROLES_DIR / file_name, size=size)


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

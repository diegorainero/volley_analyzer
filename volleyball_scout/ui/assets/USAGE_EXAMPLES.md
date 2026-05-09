# 📖 Assets Module - Esempi di Utilizzo

Questo documento mostra come utilizzare il modulo `assets` nell'applicazione Volleyball Scout.

## Importazioni base

```python
from volleyball_scout.ui.assets import get_logo_pixmap, get_logo_icon, get_icon
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
```

## Esempio 1: Visualizzare il logo nella Dashboard

```python
from volleyball_scout.ui.assets import get_logo_pixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout

# Creare un widget
dashboard_layout = QVBoxLayout()

# Caricare il logo
logo_pixmap = get_logo_pixmap(size=100)  # 100 pixel

# Creare un label e impostare il logo
logo_label = QLabel()
logo_label.setPixmap(logo_pixmap)

# Aggiungere al layout
dashboard_layout.addWidget(logo_label)
```

## Esempio 2: Impostare l'icona della finestra

```python
from volleyball_scout.ui.assets import get_logo_icon
from PyQt6.QtWidgets import QMainWindow

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Impostare l'icona della finestra
        icon = get_logo_icon(size=32)
        self.setWindowIcon(icon)
        
        self.setWindowTitle("🏐 Volleyball Scout")
```

## Esempio 3: Usare icone nei menu

```python
from volleyball_scout.ui.assets import get_icon
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMenu

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Creare un menu
        menubar = self.menuBar()
        view_menu = menubar.addMenu("Visualizza")
        
        # Aggiungere azioni con icone
        action_dashboard = QAction("Dashboard", self)
        # icon = get_icon('dashboard')  # Non ancora implementato per icone individuali
        # action_dashboard.setIcon(icon)
        view_menu.addAction(action_dashboard)
```

## Esempio 4: Creare widget con logo

```python
from volleyball_scout.ui.assets import get_logo_pixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

def create_header_widget():
    """Crea un widget header con logo"""
    header = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Logo
    logo_pixmap = get_logo_pixmap(size=60)
    logo_label = QLabel()
    logo_label.setPixmap(logo_pixmap)
    
    # Titolo
    title_label = QLabel("🏐 Volleyball Scout")
    title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
    
    layout.addWidget(logo_label)
    layout.addWidget(title_label)
    header.setLayout(layout)
    
    return header
```

## Esempio 5: Asset responsivo (scalabile)

```python
from volleyball_scout.ui.assets import get_logo_pixmap

# Diverse dimensioni a seconda del contesto
logo_small = get_logo_pixmap(size=32)      # Per toolbar
logo_medium = get_logo_pixmap(size=64)     # Per dialogs
logo_large = get_logo_pixmap(size=128)     # Per dashboard

# Gli SVG mantengono la qualità a qualsiasi dimensione
```

## Esempio 6: Gestire errori nel caricamento

```python
from volleyball_scout.ui.assets import get_logo_pixmap, get_logo_icon

def load_logo_safe(size=80):
    """Carica il logo con fallback"""
    try:
        logo = get_logo_pixmap(size=size)
        if logo.isNull():
            print("⚠️ Logo pixmap è vuoto")
            return create_placeholder(size)
        return logo
    except Exception as e:
        print(f"❌ Errore caricamento logo: {e}")
        return create_placeholder(size)

def create_placeholder(size):
    """Crea un pixmap placeholder"""
    from PyQt6.QtGui import QPixmap, QColor
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor("#252525"))
    return pixmap
```

## Esempio 7: Aggiungere nuove icone

Se vuoi aggiungere nuove icone al modulo:

### Step 1: Creare il file SVG
Crea `volleyball_scout/ui/assets/new_icon.svg`

### Step 2: Aggiornare `__init__.py`
```python
def get_new_icon() -> QIcon:
    """
    Load a custom icon
    
    Returns:
        QIcon of the custom icon
    """
    icon_path = ASSETS_DIR / "new_icon.svg"
    
    if not icon_path.exists():
        return QIcon()
    
    pixmap = QPixmap(str(icon_path))
    
    if not pixmap.isNull():
        pixmap = pixmap.scaledToHeight(
            24,
            Qt.TransformationMode.SmoothTransformation
        )
        return QIcon(pixmap)
    
    return QIcon()
```

### Step 3: Usare nel codice
```python
from volleyball_scout.ui.assets import get_new_icon

icon = get_new_icon()
button.setIcon(icon)
```

## Esempio 8: Dashboard con card e logo

```python
from volleyball_scout.ui.assets import get_logo_pixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

def create_dashboard():
    """Crea una dashboard con logo e card"""
    dashboard = QWidget()
    main_layout = QVBoxLayout()
    
    # Logo section
    logo_layout = QHBoxLayout()
    logo_layout.addStretch()
    
    logo_pixmap = get_logo_pixmap(80)
    logo_label = QLabel()
    logo_label.setPixmap(logo_pixmap)
    logo_layout.addWidget(logo_label)
    logo_layout.addStretch()
    
    main_layout.addLayout(logo_layout)
    
    # Title
    title = QLabel("🏐 Volleyball Scout - Dashboard")
    title_font = QFont()
    title_font.setPointSize(18)
    title_font.setBold(True)
    title.setFont(title_font)
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(title)
    
    # Cards
    cards_layout = QGridLayout()
    
    # Card 1
    card1 = create_card("👥 Teams", "Gestisci squadre e giocatori")
    cards_layout.addWidget(card1, 0, 0)
    
    # Card 2
    card2 = create_card("📋 Roster", "Configura gli elenchi")
    cards_layout.addWidget(card2, 0, 1)
    
    # ... più card ...
    
    main_layout.addLayout(cards_layout)
    dashboard.setLayout(main_layout)
    
    return dashboard

def create_card(title, description):
    """Helper per creare una card"""
    card = QWidget()
    layout = QVBoxLayout()
    
    title_label = QLabel(title)
    title_font = QFont()
    title_font.setPointSize(12)
    title_font.setBold(True)
    title_label.setFont(title_font)
    layout.addWidget(title_label)
    
    desc_label = QLabel(description)
    desc_label.setStyleSheet("color: #999999; font-size: 11px;")
    layout.addWidget(desc_label)
    layout.addStretch()
    
    card.setLayout(layout)
    card.setStyleSheet("""
        QWidget {
            background-color: #252525;
            border: 1px solid #3d3d3d;
            border-radius: 8px;
            padding: 15px;
        }
    """)
    
    return card
```

## Performance Tips

### 1. Caching dei pixmap
```python
# ❌ Male: Carica il logo ogni volta
for i in range(10):
    logo = get_logo_pixmap(80)

# ✅ Bene: Caricare una volta e riutilizzare
logo = get_logo_pixmap(80)
for i in range(10):
    label.setPixmap(logo)
```

### 2. Usare QIcon per Qt caching automatico
```python
# Qt cachea automaticamente gli icon
icon = get_logo_icon(32)
button1.setIcon(icon)
button2.setIcon(icon)  # Reusa la cache
```

### 3. Dimensioni SVG ottimali
```python
# SVG scalabili, ma è meglio specificare la dimensione finale
# piuttosto che scalare dinamicamente ogni volta
logo_dashboard = get_logo_pixmap(80)   # Una volta per la dashboard
logo_menu = get_logo_pixmap(24)        # Una volta per i menu
```

## Testing

### Test import
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from volleyball_scout.ui.assets import get_logo_pixmap, get_logo_icon

# Test logo pixmap
logo = get_logo_pixmap(100)
assert not logo.isNull(), "Logo pixmap is null"
print(f"✅ Logo pixmap loaded: {logo.width()}x{logo.height()}")

# Test logo icon
icon = get_logo_icon(32)
print(f"✅ Logo icon loaded")
```

### Test assets directory
```python
from pathlib import Path
from volleyball_scout.ui.assets import ASSETS_DIR

print(f"Assets directory: {ASSETS_DIR}")

# Verificare i file
for svg_file in ASSETS_DIR.glob("*.svg"):
    print(f"  ✅ {svg_file.name} ({svg_file.stat().st_size} bytes)")
```

## Common Issues & Solutions

### Issue: "QXcbConnection: Could not connect to display"
**Causa:** Trying to run GUI without display (es. in SSH)
**Soluzione:** Usare `QT_QPA_PLATFORM=offscreen` per testing

### Issue: "logo.svg not found"
**Causa:** Path relativo non corretto
**Soluzione:** Usare `Path(__file__).parent` per path assoluti

### Issue: SVG rendering quality issues
**Causa:** SVG con elementi raster invece di vettoriali
**Soluzione:** Usare solo elementi SVG vettoriali (paths, shapes, text)

---

**Ultimo aggiornamento:** 2024
**Stato:** ✅ Documentazione completa

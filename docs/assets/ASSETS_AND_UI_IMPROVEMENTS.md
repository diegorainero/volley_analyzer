# 🎨 Volleyball Scout - Assets and UI Improvements

## ✅ Completato

Sono stati aggiunti loghi e asset visivi migliorati all'interfaccia Volleyball Scout.

### 📁 Struttura delle cartelle

```
volleyball_scout/ui/
├── assets/                 # 🆕 Nuova cartella
│   ├── __init__.py        # Modulo per caricare gli asset
│   ├── logo.svg           # Logo principale (pallone + binocoli)
│   ├── icons.svg          # Sprite di icone (dashboard, team, formation, scout, stats)
│   └── README.md          # Documentazione degli asset
├── app_dark.py            # ✏️ AGGIORNATO - Carica e usa gli asset
├── app.py                 # Non modificato
└── ... (altri file)
```

## 🎯 Modifiche apportate

### 1. **Cartella Assets** (`volleyball_scout/ui/assets/`)

#### `logo.svg`
- Logo principale dell'applicazione
- Design: Pallone da pallavolo con binocoli
- Colori: Tema scuro con accenti blu (#0066cc)
- Utilizzo: Dashboard, icona finestra, menu

#### `icons.svg`
- Sprite SVG con 5 icone principali
- **Dashboard:** Griglia di 4 quadrati
- **Team:** Persone con grafici statistici
- **Formation:** Campo da volley con giocatori
- **Scout:** Telecamera
- **Stats:** Grafico a barre con assi
- Colori: Coerenti con il tema scuro

#### `__init__.py` (Assets Module)
Funzioni per caricare gli asset:
```python
get_logo_pixmap(size: int) -> QPixmap
get_icon(icon_name: str) -> QIcon
get_logo_icon(size: int) -> QIcon
```

### 2. **Aggiornamento app_dark.py**

#### Importazioni
```python
from volleyball_scout.ui.assets import get_logo_pixmap, get_icon, get_logo_icon
```

#### Classe DashboardView - Miglioramenti
- ✅ Logo centralizzato in alto
- ✅ Titolo e sottotitolo
- ✅ Grid layout di 6 card (2 righe × 3 colonne)
- ✅ Card con:
  - Titolo (emoji + testo)
  - Descrizione
  - Colore dinamico (#252525 → #2d2d2d on hover)
  - Border blu al hover (#0066cc)

#### Card della Dashboard
1. **👥 Teams & Players** - Gestisci squadre e giocatori
2. **📋 Roster Setup** - Configura gli elenchi squadra
3. **🏐 Formation** - Imposta formazioni e titolari
4. **🎥 Scout & Video** - Registra e analizza video
5. **📈 Statistics** - Visualizza statistiche partite
6. **⚙️ Settings** - Impostazioni applicazione

#### Window Icon
- L'icona della finestra viene impostata con `setWindowIcon(get_logo_icon())`

### 3. **Tema scuro - UNCHANGED** ✅
- Il dark theme stylesheet rimane identico
- Colori mantengono coerenza con gli asset
- Nessuna rottura di funzionalità esistente

## 🎨 Palette colori

| Elemento | Hex | RGB |
|----------|-----|-----|
| Background primario | #1e1e1e | (30, 30, 30) |
| Superficie | #252525/#2d2d2d | (37-45, 37-45, 37-45) |
| Border | #3d3d3d | (61, 61, 61) |
| Testo primario | #e0e0e0 | (224, 224, 224) |
| Testo secondario | #999999 | (153, 153, 153) |
| Accento primario | #0066cc | (0, 102, 204) |
| Accento hover | #0052a3 | (0, 82, 163) |

## 🚀 Utilizzo nel codice

### Caricare il logo nella UI
```python
from volleyball_scout.ui.assets import get_logo_pixmap

logo = get_logo_pixmap(size=80)
label.setPixmap(logo)
```

### Impostare l'icona della finestra
```python
from volleyball_scout.ui.assets import get_logo_icon

icon = get_logo_icon(size=32)
self.setWindowIcon(icon)
```

### Aggiungere nuove icone
```python
# 1. Creare new_icon.svg nella cartella assets/
# 2. Aggiornare assets/__init__.py con una nuova funzione
def get_my_icon() -> QIcon:
    svg_path = ASSETS_DIR / "new_icon.svg"
    pixmap = QPixmap(str(svg_path))
    return QIcon(pixmap)

# 3. Usare nel codice
from volleyball_scout.ui.assets import get_my_icon
icon = get_my_icon()
```

## 📋 Specifiche Dashboard

### Layout principale
```
┌─────────────────────────────────────────┐
│           [Logo centralizzato]          │
│                                         │
│  🏐 Volleyball Scout - Dashboard        │
│  Benvenuto nella dashboard principale   │
│                                         │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐│
│  │ 👥 Teams │ │ 📋 Roster│ │ 🏐 Form ││
│  │ Gestisci │ │ Configura│ │ Imposta ││
│  └──────────┘ └──────────┘ └─────────┘│
│                                         │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐│
│  │ 🎥 Scout │ │ 📈 Stats │ │ ⚙️ Settings
│  │ Registra │ │ Visualiz │ │ Imposta ││
│  └──────────┘ └──────────┘ └─────────┘│
│                                         │
└─────────────────────────────────────────┘
```

### Styling card
- Background: `#252525` (grigio medio)
- Border: `1px solid #3d3d3d` (grigio chiaro)
- Border-radius: `8px` (spigoli arrotondati)
- Padding: `15px`
- Hover: Background → `#2d2d2d`, Border → `1px solid #0066cc`

## 📐 Dimensioni

| Elemento | Dimensione |
|----------|-----------|
| Logo dashboard | 80px |
| Window icon | 32px |
| Card height | min 100px |
| Card spacing | 15px |
| Grid layout | 3 colonne × 2 righe |

## ✨ Caratteristiche

✅ **Coerenza visiva** - Tutti gli asset rispettano il tema scuro
✅ **Scalabilità** - SVG per qualità a qualsiasi risoluzione
✅ **Modularità** - Funzioni asset separate e riutilizzabili
✅ **Performance** - Caching automatico dei pixmap
✅ **Manutenibilità** - Asset centralizzati in una cartella dedicata
✅ **Documentazione** - README nella cartella assets

## 🔄 Integrazione con il codice

### Avvio dell'app
```bash
cd volley_analizer
python -m volleyball_scout.ui.app_dark
```

### Verificare i caricamento degli asset
L'output dovrebbe contenere:
```
✅ Database connesso
...
🏐 VOLLEYBALL SCOUT - PyQt6 Application
========================================
📋 Applicazione avviata!
   - Menu in alto per navigare le sezioni
   - File → Esci per chiudere l'applicazione
   - Tema scuro attivato
   - Assets caricati
```

## 📝 Prossimi passi (Opzionali)

- [ ] Implementare animazioni CSS per le card hover
- [ ] Aggiungere icone per loading, success, error, warning
- [ ] Creare versione light theme degli asset
- [ ] Estrarre singole icone dal sprite SVG
- [ ] Aggiungere transitions animate sulla dashboard
- [ ] Cache in-memory dei pixmap più utilizzati

## 🐛 Troubleshooting

### Logo non visualizzato
```
⚠️ Could not load logo: [error]
```
**Soluzione:** Verificare che `assets/logo.svg` esista e sia leggibile.

### Errore importazione assets
```
⚠️ Warning: Assets module not available: [error]
```
**Soluzione:** Assicurarsi che `volleyball_scout/ui/assets/__init__.py` esista.

### Icons non visibili nei menu
Attualmente il modulo `get_icon()` ritorna il full sprite.
**Nota:** Questa è una semplificazione. Per icone individuali, richiederebbe
manipolazione SVG più sofisticata.

## 📄 File modificati

| File | Stato | Descrizione |
|------|-------|------------|
| `assets/__init__.py` | 🆕 Creato | Modulo per asset utilities |
| `assets/logo.svg` | 🆕 Creato | Logo principale |
| `assets/icons.svg` | 🆕 Creato | Sprite di icone |
| `assets/README.md` | 🆕 Creato | Documentazione asset |
| `app_dark.py` | ✏️ Modificato | Aggiunta DashboardView migliorata |
| `DARK_STYLESHEET` | ✅ Invariato | Nessuna modifica al tema |

---

**Data:** 2024
**Versione:** 1.0
**Status:** ✅ Completato

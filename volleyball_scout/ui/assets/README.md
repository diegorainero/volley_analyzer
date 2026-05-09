# Volleyball Scout Assets

Cartella contenente i file di design e le icone per l'interfaccia Volleyball Scout.

## File disponibili

### `logo.svg`
Logo principale dell'applicazione Volleyball Scout:
- **Scopo:** Visualizzato nella dashboard, nella finestra e nei menu
- **Dimensioni:** SVG scalabile (vedi `get_logo_pixmap()` per le dimensioni di rendering)
- **Colori:** Tema scuro (#1e1e1e) con accenti blu (#0066cc)
- **Elementi:** Pallone da pallavolo + binocoli (rappresenta il "scout")

### `icons.svg`
Sprite SVG contenente le icone per i menu e i pulsanti:
- **Dashboard:** Griglia di 4 quadrati (rappresenta le sezioni)
- **Team:** Silhouette di persone con grafici a barre
- **Formation:** Campo da pallavolo con giocatori
- **Scout:** Telecamera professionale
- **Stats:** Grafico a barre con assi

Tutte le icone usano il colore primary #0066cc.

## Come usare gli asset

### Nel codice Python

```python
from volleyball_scout.ui.assets import (
    get_logo_pixmap,
    get_logo_icon,
    get_icon
)

# Carica il logo come pixmap (per visualizzare)
logo = get_logo_pixmap(size=80)  # 80px
label.setPixmap(logo)

# Carica il logo come icona
icon = get_logo_icon(size=32)
window.setWindowIcon(icon)

# Carica un'icona specifica (non ancora implementato per singole icone)
# dashboard_icon = get_icon('dashboard')
```

### Modificare gli asset

Per modificare i file SVG:
1. Usare un editor SVG (Inkscape, Adobe XD, Figma, VS Code con extension)
2. **Importante:** Mantenere i colori coerenti:
   - Background scuro: `#1e1e1e`
   - Colore primary: `#0066cc`
   - Colore testo: `#e0e0e0`
   - Border: `#3d3d3d`
3. Salvare e ricaricare l'app

## Color Scheme

Per coerenza con il tema scuro dell'app:

| Elemento | Colore | Hex |
|----------|--------|-----|
| Background | Grigio scuro | #1e1e1e |
| Superficie | Grigio medio | #252525/#2d2d2d |
| Borders | Grigio chiaro | #3d3d3d |
| Testo primario | Bianco sporco | #e0e0e0 |
| Testo secondario | Grigio | #999999/#666666 |
| Accento primario | Blu | #0066cc |
| Hover | Blu scuro | #0052a3 |

## Aggiungere nuovi asset

Per aggiungere nuove icone o logo:

1. **Creare il file SVG:** `new_asset.svg`
2. **Aggiungerlo alla cartella:** `volleyball_scout/ui/assets/`
3. **Aggiornare `__init__.py`:** Aggiungere una funzione getter
4. **Importare nel file UI:** 
   ```python
   from volleyball_scout.ui.assets import get_new_asset
   ```
5. **Usare nel codice:** 
   ```python
   asset = get_new_asset()
   ```

## Performance

- Gli SVG sono scalabili senza perdita di qualità
- I QPixmap vengono cachati automaticamente da PyQt6
- Per asset complessi, valutare il pre-rendering in PNG se necessario

## Future improvements

- [ ] Individuare le singole icone nel sprite SVG
- [ ] Aggiungere animazioni per alcune icone
- [ ] Creare versioni alternative (light theme)
- [ ] Aggiungere icone per altri elementi UI (loading, success, error, warning)

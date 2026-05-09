# 🏐 Volleyball Scout Assets - Quick Start Guide

Guida rapida per iniziare con i nuovi asset e l'interfaccia migliorata.

---

## 🚀 Avvio veloce (30 secondi)

```bash
# 1. Entrare nella directory
cd volley_analizer

# 2. Avviare l'applicazione
python -m volleyball_scout.ui.app_dark

# 3. Aprire il browser e navigare alla dashboard
# (oppure semplicemente vedere la finestra PyQt6 aprirsi)
```

**Dovresti vedere:**
- ✅ Logo centralizzato in alto (pallone + binocoli)
- ✅ Titolo "🏐 Volleyball Scout - Dashboard"
- ✅ 6 card colorate in griglia
- ✅ Tema scuro coerente

---

## 📁 Cosa è stato aggiunto

### Cartella Assets
```
volleyball_scout/ui/assets/
├── logo.svg              # Logo principale (pallone + binocoli)
├── icons.svg             # Sprite di 5 icone
├── __init__.py           # Modulo per caricare gli asset
├── README.md             # Documentazione
└── USAGE_EXAMPLES.md     # Esempi di utilizzo
```

### File Python
```
app_dark.py              # ✏️ AGGIORNATO - DashboardView migliorata
TEST_ASSETS.py           # Test suite
```

### Documentazione
```
ASSETS_AND_UI_IMPROVEMENTS.md       # Dettagli cambiamenti
VOLLEYBALL_SCOUT_ASSETS_DEPLOYMENT.md  # Deployment guide
ASSETS_IMPLEMENTATION_SUMMARY.md    # Riepilogo implementazione
QUICK_START_ASSETS.md               # Questo file
```

---

## 🎯 Cosa fare adesso

### 1. **Verificare l'installazione** (1 min)

```bash
# Run il test suite
python volleyball_scout/ui/TEST_ASSETS.py

# Output atteso: ✅ PASS per tutti i test
```

### 2. **Esplorare il codice** (5 min)

Aprire questi file per capire come funziona:

```python
# Modulo asset
cat volleyball_scout/ui/assets/__init__.py

# DashboardView migliorata
grep -A 30 "class DashboardView" volleyball_scout/ui/app_dark.py

# Uso del logo
grep "get_logo_pixmap" volleyball_scout/ui/app_dark.py
```

### 3. **Leggere la documentazione** (10 min)

Consigliato in questo ordine:
1. `volleyball_scout/ui/assets/README.md` - Panoramica
2. `volleyball_scout/ui/assets/USAGE_EXAMPLES.md` - Come usare
3. `ASSETS_AND_UI_IMPROVEMENTS.md` - Dettagli tecnici

### 4. **Personalizzare** (15 min)

Modificare il design:
- Editare i colori nei file SVG
- Cambiare il testo delle card
- Aggiungere nuove icone

---

## 💡 Utilizzo nel codice

### Caricare il logo

```python
from volleyball_scout.ui.assets import get_logo_pixmap

# Dimensioni disponibili: 32, 64, 80, 100, 128, ...
logo = get_logo_pixmap(size=80)

# Usare nella UI
label = QLabel()
label.setPixmap(logo)
```

### Impostare l'icona finestra

```python
from volleyball_scout.ui.assets import get_logo_icon

icon = get_logo_icon(size=32)
window.setWindowIcon(icon)
```

### Aggiungere una nuova icona

1. Creare `assets/new_icon.svg`
2. Aggiungere funzione in `assets/__init__.py`
3. Importare e usare nel codice

Vedi `assets/USAGE_EXAMPLES.md` per dettagli.

---

## 🎨 Colori usati

Tema scuro professionale:

| Elemento | Colore | Hex |
|----------|--------|-----|
| Background | Grigio scuro | #1e1e1e |
| Surface | Grigio medio | #252525 |
| Border | Grigio chiaro | #3d3d3d |
| Testo | Bianco sporco | #e0e0e0 |
| Accento | Blu | #0066cc |

---

## ✨ Dashboard Feature

La nuova dashboard contiene 6 card:

1. **👥 Teams & Players** - Gestisci squadre
2. **📋 Roster Setup** - Configura elenchi
3. **🏐 Formation** - Imposta formazioni
4. **🎥 Scout & Video** - Registra video
5. **📈 Statistics** - Visualizza stats
6. **⚙️ Settings** - Impostazioni

Ogni card ha:
- Titolo emoji + testo
- Descrizione
- Styling hover interattivo
- Background scuro coerente

---

## 🔧 Troubleshooting

### P: Il logo non si visualizza
**R:** Verificare che `assets/logo.svg` esista

### P: ImportError dal modulo
**R:** Assicurarsi che `assets/__init__.py` esista

### P: Colori non corretti
**R:** Verificare la palette di colori in `assets/README.md`

### P: SVG non renderizzato
**R:** Usare un editor online SVG validator per verificare sintassi

---

## 📊 Stats

```
📁 Cartella assets:     1 nuova
📄 File SVG:            2
📄 Linee codice:        ~200
📄 Documentazione:      ~1000 linee
🧪 Test case:           7
⏱️  Load time:           <10ms
💾 Size:                ~40 KB
```

---

## 🎓 Learning Path

**Principiante (5 min):**
- Leggere `assets/README.md`
- Eseguire `TEST_ASSETS.py`
- Avviare l'app

**Intermedio (20 min):**
- Leggere `USAGE_EXAMPLES.md`
- Capire come caricare gli asset
- Aggiungere una nuova icona

**Avanzato (1 ora):**
- Leggere `ASSETS_IMPLEMENTATION_SUMMARY.md`
- Creare un tema personalizzato
- Ottimizzare gli SVG

---

## 📞 Quick Help

**Come... aggiungere una nuova card?**
Vedi: `app_dark.py` → `DashboardView._create_card_widget()`

**Come... cambiare i colori?**
Vedi: `assets/README.md` → Color Scheme section

**Come... modificare il logo?**
Vedi: `assets/logo.svg` (editare con VS Code / Inkscape)

**Come... caricare un'icona?**
Vedi: `assets/USAGE_EXAMPLES.md` → Esempio 2 & 7

---

## ✅ Checklist

- [ ] Eseguire `TEST_ASSETS.py` e verificare ✅ PASS
- [ ] Avviare `app_dark.py` e vedere la dashboard
- [ ] Leggere `assets/README.md`
- [ ] Leggere `USAGE_EXAMPLES.md`
- [ ] Personalizzare i colori (opzionale)
- [ ] Aggiungere una nuova icona (opzionale)

---

## 🚀 Prossimi Step

**Subito:**
```bash
python -m volleyball_scout.ui.app_dark
```

**Poi:**
- Leggi la documentazione nella cartella assets
- Personalizza i colori e il testo
- Aggiungi le tue icone

**Infine:**
- Deploy in produzione
- Raccogli feedback
- Migliora il design

---

## 📚 Tutti i File

| File | Descrizione |
|------|------------|
| `volleyball_scout/ui/assets/` | Cartella principale |
| `logo.svg` | Logo principale |
| `icons.svg` | Sprite icone |
| `__init__.py` | Modulo asset utilities |
| `README.md` | Documentazione |
| `USAGE_EXAMPLES.md` | Esempi |
| `app_dark.py` | App migliorata |
| `TEST_ASSETS.py` | Test suite |

---

**Versione:** 1.0
**Status:** ✅ Pronto per l'uso
**Data:** 2024

🎉 **Divertiti a sviluppare!**

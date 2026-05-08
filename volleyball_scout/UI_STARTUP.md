# 🏐 Volleyball Scout UI - Guida di Avvio

## ⚙️ Prerequisiti

Prima di avviare l'interfaccia grafica, assicurati di avere installato:

```bash
pip install PyQt6 SQLAlchemy
```

## 🚀 Avvio dell'Applicazione

Ci sono due modi per lanciare l'applicazione:

### Metodo 1: Script Launcher (Consigliato)

```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
python3 volleyball_scout/run_ui.py
```

### Metodo 2: Diretto

```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
python3 volleyball_scout/ui/app.py
```

### Metodo 3: Come modulo

```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
python3 -m volleyball_scout.run_ui
```

## 📊 Interfaccia Dashboard

Quando avvii l'app, vedrai una finestra con due pannelli:

### 🔴 Pannello Sinistro: Griglia Match

Una griglia scrollabile di 4 colonne che mostra **TUTTI i match** del database, con colori diversi in base allo stato:

```
┌─────────────────────────────────────────┐
│  14/12/2024    │  15/12/2024    │  ... │
│  Team A vs B   │  Team C vs D   │      │
│  ✅ Completato │  ⏳ In Corso    │      │
└─────────────────────────────────────────┘
│  17/12/2024    │  18/12/2024    │  ... │
│  Team E vs F   │  Team G vs H   │      │
│  🔲 Bozza      │  ✅ Completato │      │
└─────────────────────────────────────────┘
```

**Colori:**
- 🔲 **Bozza** → Grigio (#E8E8E8)
- ⏳ **In Corso** → Giallo (#FFFACD)
- ✅ **Completato** → Verde (#C8E6C9)

**Interazione:**
- Click su un match per aprire lo scout
- Hover mostra bordo blu
- Scroll verticale per più match

### 📝 Pannello Destro: Sessioni in Bozza

Lista delle sessioni di scout in corso:

```
┌──────────────────────────┐
│ 📝 Sessioni in Bozza     │
├──────────────────────────┤
│ ▶️ Team A vs Team B      │
│    Data: 14/12/2024      │
│    Ultimi eventi: 42     │
├──────────────────────────┤
│ 📝 Team C vs Team D      │
│    Data: 15/12/2024      │
│    Ultimi eventi: 0      │
├──────────────────────────┤
│ [▶ Riprendi] [🗑 Elimina]│
└──────────────────────────┘
```

**Azioni:**
- Clicca una sessione per selezionarla
- **▶ Riprendi**: Continua da dove hai lasciato
- **🗑 Elimina**: Cancella la sessione (non annullabile)

## 💡 Funzionalità

### Match Grid
✅ Carica tutti i match dal database  
✅ Ordinati per data decrescente  
✅ Colori diversi in base allo stato  
✅ Hover effects  
✅ Click per selezionare  
✅ Scroll verticale per molti match  

### Draft Management
✅ Auto-salvataggio  
✅ Riprendi dalle ultime modifiche  
✅ Elimina bozze non volute  
✅ Conta degli ultimi eventi  

### Database Integration
✅ Connessione automatica a SQLite locale  
✅ Fallback a PostgreSQL se DATABASE_URL è configurata  
✅ Creazione automatica di tabelle  
✅ Session management automatico  

## 🐛 Troubleshooting

### Errore: ModuleNotFoundError: No module named 'PyQt6'

**Soluzione:**
```bash
pip install PyQt6
```

### Errore: ModuleNotFoundError: No module named 'sqlalchemy'

**Soluzione:**
```bash
pip install SQLAlchemy
```

### Errore: Database connection failed

**Soluzione:**
1. Verifica che `~/.volleyball_scout/data/scout.db` esista
2. Controlla i permessi della cartella
3. Se usi PostgreSQL, verifica `DATABASE_URL`

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/volleyball_scout"
```

### La finestra non appare

**Soluzione:**
1. Controlla che nessun'altra istanza sia in esecuzione
2. Prova a lanciare da terminale e leggi gli errori
3. Aumenta la risoluzione del monitor

## 📂 File Moduli

| File | Descrizione |
|------|-------------|
| `volleyball_scout/ui/app.py` | Main app con dashboard |
| `volleyball_scout/ui/matches_grid.py` | Widget griglia match |
| `volleyball_scout/ui/formation_panel.py` | Panel formazione |
| `volleyball_scout/ui/drafts/` | Gestione bozze |
| `volleyball_scout/run_ui.py` | Script launcher |
| `volleyball_scout/core/database.py` | Database manager |

## 🔧 Sviluppo

### Aggiungere nuovi widget

```python
from volleyball_scout.ui.app import DashboardView

class MioWidget(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        # Implementazione...

# Aggiungi a DashboardView
```

### Testare singoli widget

```python
# Test MatchesGridWidget
from volleyball_scout.ui.matches_grid import MatchesGridWidget
from volleyball_scout.core.database import DatabaseManager

db = DatabaseManager()
widget = MatchesGridWidget(db)
widget.show()
```

## 📞 Supporto

Per problemi o domande:
1. Controlla il file `~/.volleyball_scout/scout.log`
2. Leggi i messaggi di errore nel terminale
3. Verifica che il database sia accessibile

---

**Versione:** 0.1  
**Ultimo aggiornamento:** 2024  
**Stato:** Pronto per il test

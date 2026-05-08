# 📦 Database Check Tools - Riepilogo

Questo documento riassume tutti gli strumenti creati per verificare i dati nel database.

---

## ✨ Cosa è Stato Creato

### 1. 🖥️ **check_database.py** (CLI Script)
**File:** `volley_analizer/check_database.py`

Script a riga di comando che mostra i dati del database nel terminale.

**Esecuzione:**
```bash
cd volley_analizer
python3 check_database.py
```

**Output:**
- Informazioni connessione database
- Elenco squadre con conteggio giocatori
- Giocatori per squadra (numero, nome, cognome, ruolo, libero, capitano)
- Elenco partite

**Vantaggi:**
- ✅ Nessuna dipendenza grafica
- ✅ Veloce e leggero
- ✅ Funziona su server senza GUI
- ✅ Output copiabile/esportabile
- ✅ Perfetto per debugging

**Quando usarlo:**
- Verifiche rapide dal terminale
- Script di automazione
- Server senza interfaccia grafica
- Logging/debugging

---

### 2. 🎨 **check_database_ui.py** (GUI PyQt6)
**File:** `volley_analizer/check_database_ui.py`

Interfaccia grafica per visualizzare i dati in modo intuitivo.

**Esecuzione:**
```bash
cd volley_analizer
python3 check_database_ui.py
```

**Interfaccia:**
```
┌─────────────────────────────────────────────────────────────┐
│ ✅ Database connesso: SQLite (...)                          │
├─────────────────────────────────────────────────────────────┤
│ [Squadre]  [Giocatori]  [Partite]                           │
├─────────────────────────────────────────────────────────────┤
│ ID | Nome | Categoria | Impianto | Giocatori              │
│ 1  | Attacco | Test | Palazzetto | 7                       │
│                                    [🔄 Aggiorna Dati]       │
└─────────────────────────────────────────────────────────────┘
```

**Funzionalità:**
- 📊 Tab Squadre - Lista con ID, Nome, Categoria, Impianto, Conteggio Giocatori
- 👥 Tab Giocatori - Lista con Squadra, #, Nome, Cognome, Ruolo, Libero, Capitano
- 🏐 Tab Partite - Lista con ID, Casa, Trasferta, Data, Stato
- 🔄 Pulsante Aggiorna - Ricaricare i dati dal database
- ℹ️ Header - Informazioni sulla connessione

**Vantaggi:**
- ✅ Interfaccia visuale e intuitiva
- ✅ Tabelle ben formattate
- ✅ Colonne ridimensionabili
- ✅ Refresh in tempo reale
- ✅ Gestione errori visuale
- ✅ Multipli tab per organizzazione

**Quando usarlo:**
- Visualizzazione rapida e intuitiva
- Verificare dati prima di operazioni
- Gestione grafica dei dati
- Testing durante sviluppo

---

### 3. 🚀 **launch_database_check.py** (Launcher)
**File:** `volley_analizer/launch_database_check.py`

Script launcher per avviare facilmente il database check UI.

**Esecuzione:**
```bash
cd volley_analizer
python3 launch_database_check.py
```

**Scopo:**
- Entry point conveniente per l'utente
- Configurazione imports centralizzata
- Facilita aggiunta di opzioni future (CLI, GUI, etc.)

---

## 📖 Documentazione Creata

### 4. 📘 **README_DATABASE_CHECK.md** (Quick Start)
**File:** `volley_analizer/README_DATABASE_CHECK.md`

Guida rapida per l'utente finale.

**Contiene:**
- Istruzioni di quick start (30 secondi)
- Descrizione di cosa vedi in ogni tab
- Esempi di dati
- Setup iniziale (una sola volta)
- Casi d'uso comuni
- Troubleshooting rapido
- Pro tips
- Prossimi passi

**Target:** Utenti finali che vogliono verificare velocemente i dati

---

### 5. 📙 **DATABASE_CHECK_GUIDE.md** (Guida Completa)
**File:** `volley_analizer/DATABASE_CHECK_GUIDE.md`

Guida approfondita con spiegazioni dettagliate.

**Contiene:**
- Requisiti e dipendenze
- Opzione CLI completa
- Opzione GUI completa
- Struttura database (schema SQL)
- Posizioni database (SQLite vs PostgreSQL)
- Troubleshooting dettagliato
- Tips e integrazioni
- Riferimenti ai file sorgente

**Target:** Sviluppatori e utenti avanzati

---

### 6. 📘 **TOOLS_SUMMARY.md** (Panoramica Completa)
**File:** `volley_analizer/TOOLS_SUMMARY.md`

Panoramica completa di tutti gli strumenti disponibili nel progetto.

**Contiene:**
- Launcher principali (Volleyball Scout UI)
- Database Check Tools (CLI e GUI)
- Database Management API
- Alembic Migrations
- SQLAlchemy Models
- Use cases con esempi di codice
- File structure
- Data flow
- Configuration
- Documentazione aggiuntiva
- Checklist rapida

**Target:** Sviluppatori che vogliono una visione completa

---

## 🛠️ Utilità Fornite

### DatabaseManager API
Classe in `volleyball_scout/core/database.py` che fornisce:
- `get_session()` - Ottiene una sessione SQLAlchemy
- `session_scope()` - Context manager con auto commit/rollback
- `ping()` - Verifica connessione
- `get_db_info()` - Informazioni connessione (type, url, connected)
- Support per SQLite (default) e PostgreSQL (cloud)

### Models (ORM)
Modelli SQLAlchemy in `volleyball_scout/core/models.py`:
- `Team` - Squadre con relazioni a players e matches
- `Player` - Giocatori con relazione a team
- `Match` - Partite con squadre home/away
- `MatchSet` - Set di una partita
- `ScoutEvent` - Eventi DataVolley
- `MatchPlayer` - Giocatori in una partita

---

## 📊 Struttura File

```
volley_analizer/
├── check_database.py                      🖥️ CLI Tool
├── check_database_ui.py                   🎨 GUI Tool
├── launch_database_check.py               🚀 Launcher
│
├── README_DATABASE_CHECK.md               📖 Quick Start
├── DATABASE_CHECK_GUIDE.md                📙 Guida Completa
├── DATABASE_CHECK_SUMMARY.md              📘 Questo file
├── TOOLS_SUMMARY.md                       📘 Panoramica Totale
│
└── volleyball_scout/
    ├── core/
    │   ├── database.py                    🗄️ DatabaseManager
    │   └── models.py                      📊 ORM Models
    └── ...
```

---

## 🎯 Quick Reference

### Per verificare rapidamente i dati

**Opzione A - GUI (Consigliato per utenti finali):**
```bash
python3 check_database_ui.py
```

**Opzione B - CLI (Consigliato per sviluppatori):**
```bash
python3 check_database.py
```

---

### Per setup iniziale

```bash
cd volley_analizer
pip install -r requirements.txt
alembic upgrade head
alembic upgrade 20260508_add_status_match_test  # Dati di test
```

---

### Per integrare nel codice

```python
from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Team, Player

db = DatabaseManager()
with db.session_scope() as session:
    teams = session.query(Team).all()
    for team in teams:
        print(f"{team.name}: {len(team.players)} giocatori")
```

---

## ✅ Checklist di Utilizzo

### Primo Utilizzo
- [ ] Installare requirements: `pip install -r requirements.txt`
- [ ] Inizializzare database: `alembic upgrade head`
- [ ] (Opzionale) Caricare dati test: `alembic upgrade 20260508_add_status_match_test`
- [ ] Eseguire check: `python3 check_database_ui.py` o `python3 check_database.py`

### Verifiche Regolari
- [ ] Eseguire uno dei check tools regolarmente
- [ ] Verificare che squadre e giocatori siano corretti
- [ ] Aggiornare dati tramite UI se necessario

### Sviluppo
- [ ] Testare integrazioni con DatabaseManager
- [ ] Verificare queries ORM
- [ ] Controllare relazioni tra modelli

---

## 🔗 Relazioni tra File

```
check_database_ui.py
    ↓ imports
volleyball_scout/core/database.py (DatabaseManager)
    ↓ uses
volleyball_scout/core/models.py (Team, Player, Match, etc.)
    ↓ maps to
SQLite Database (.volleyball_scout/data/scout.db)
    ↓ managed by
alembic/ (Migrations)

check_database.py
    ↓ imports (same as above)
```

---

## 🚀 Launcher Entry Points

Disponibili diverse modalità di esecuzione:

```bash
# Database Check GUI (Consigliato)
python3 check_database_ui.py
python3 launch_database_check.py

# Database Check CLI
python3 check_database.py

# Volleyball Scout Main App
python3 volleyball_scout/run_ui.py
python3 run_desktop.py  # (con dialogo di scelta)

# Come modulo
python3 -m volleyball_scout.ui.app
```

---

## 💡 Best Practices

### Per Sviluppatori
1. Usa `database.py` CLI per verifiche rapide
2. Usa `check_database_ui.py` per ispezioni visive
3. Usa DatabaseManager API per script
4. Usa session_scope() context manager per auto cleanup

### Per Utenti
1. Usa `check_database_ui.py` per visualizzazione intuitiva
2. Clicca "Aggiorna Dati" per ricaricare
3. Aggiungi squadre/giocatori tramite UI principale
4. Consulta le guide `.md` per troubleshooting

### Per Deployment
1. Usa CLI script in script automatizzati
2. Assicura SQL database access (SQLite local o PostgreSQL cloud)
3. Configura `DATABASE_URL` env var per cloud
4. Esegui migrazioni Alembic prima di startup

---

## 📞 Support

Consulta:
- **README_DATABASE_CHECK.md** - Guida rapida (primo riferimento)
- **DATABASE_CHECK_GUIDE.md** - Guida approfondita
- **TOOLS_SUMMARY.md** - Panoramica di tutti gli strumenti
- **volleyball_scout/core/models.py** - Riferimento modelli (docstrings)
- **volleyball_scout/core/database.py** - Riferimento API (docstrings)

---

## 🎓 Prossimi Passi

Dopo aver verificato i dati:

1. **Formation Panel** - Scegli titolari e libero
2. **Scout & Video** - Registra eventi
3. **Statistics** - Visualizza statistiche
4. **Export** - Esporta dati

Vedi **TOOLS_SUMMARY.md** per comandi dettagliati.

---

## 📝 Changelog

### Versione 1.0 (2025-01-15)
- ✅ Creato `check_database.py` (CLI)
- ✅ Creato `check_database_ui.py` (GUI)
- ✅ Creato `launch_database_check.py` (Launcher)
- ✅ Creato `README_DATABASE_CHECK.md` (Quick Start)
- ✅ Creato `DATABASE_CHECK_GUIDE.md` (Guida Completa)
- ✅ Creato `TOOLS_SUMMARY.md` (Panoramica Totale)
- ✅ Creato questo file di riepilogo

---

**Data:** 2025-01-15  
**Versione:** 1.0  
**Autore:** Sistema di Sviluppo

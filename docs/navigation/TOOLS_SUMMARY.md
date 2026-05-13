# 🏐 Volleyball Scout - Strumenti Disponibili

Questo documento riassume tutti gli strumenti e i comandi disponibili per lavorare con il Volleyball Scout.

---

## 🚀 Launcher Principali

### 1. **Volleyball Scout UI (Completo)**
Avvia l'applicazione principale con tutte le funzionalità.

```bash
# Opzione 1: Diretto dal launcher
python3 run_desktop.py
# → Scegli "Volleyball Scout" dal dialogo

# Opzione 2: Diretto da volleyball_scout
python3 volleyball_scout/run_ui.py

# Opzione 3: Come modulo
python3 -m volleyball_scout.ui.app
```

**Funzionalità:**
- 📊 Dashboard (Partite, Sessioni in Bozza)
- 👥 Gestione Squadre e Giocatori
- 📋 Setup Roster
- 🏐 Formation Panel (Selezione titolari/libero)
- 📝 Scout & Video Player
- 📈 Statistiche

---

## 🔍 Database Check Tools

### 2. **Database Check CLI (Command Line)**
Verifica i dati dal terminale in modo veloce e leggero.

```bash
python3 check_database.py
```

**Output:**
```
✅ Connessione al database riuscita!
   Database: SQLite (~/.volleyball_scout/data/scout.db)
   Connesso: True

================================================================================
  📊 SQUADRE (2)
================================================================================
ID    Nome                    Categoria    Impianto      Giocatori
1     Attacco                 Test         Palazzetto    7
2     Cihsosla Volley         Test         Palazzetto    14

================================================================================
  👥 GIOCATORI PER SQUADRA
================================================================================

🔹 Attacco (7 giocatori)
  #     Nome        Cognome     Ruolo              Libero  Capitano
  1     Marco       Rossi       Palleggiatore      -       -
  2     Andrea      Bianchi     Schiacciatore      -       -
  ...
```

**Vantaggi:**
- ✅ Leggero (no GUI)
- ✅ Funziona su server
- ✅ Output semplice e copiabile
- ✅ Perfetto per script

---

### 3. **Database Check UI (Graphical)**
Interfaccia visuale per ispezionare i dati in modo intuitivo.

```bash
# Opzione 1: Diretto
python3 check_database_ui.py

# Opzione 2: Con launcher
python3 launch_database_check.py
```

**Interfaccia:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ✅ Database connesso: SQLite (~/.volleyball_scout/data/scout.db) │
├─────────────────────────────────────────────────────────────────┤
│ [Squadre] [Giocatori] [Partite]                                  │
├─────────────────────────────────────────────────────────────────┤
│ ID | Nome              | Categoria | Impianto   | Giocatori      │
│ 1  | Attacco           | Test      | Palazzetto | 7              │
│ 2  | Cihsosla Volley   | Test      | Palazzetto | 14             │
│                                                  [🔄 Aggiorna]    │
└─────────────────────────────────────────────────────────────────┘
```

**Vantaggi:**
- ✅ Interfaccia intuitiva
- ✅ Tabelle ben formattate
- ✅ Colonne ridimensionabili
- ✅ Refresh in tempo reale
- ✅ Errori ben visualizzati

---

## 📚 Database Management

### 4. **Database Manager (API Programmatictica)**

Usa il DatabaseManager per accedere ai dati da script:

```python
from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Team, Player, Match

# Crea manager
db = DatabaseManager()

# Opzione 1: Session context manager
with db.session_scope() as session:
    teams = session.query(Team).all()
    for team in teams:
        print(f"{team.name}: {len(team.players)} giocatori")

# Opzione 2: Session manuale
session = db.get_session()
matches = session.query(Match).all()
session.close()

# Verifica connessione
if db.ping():
    print("✅ Database connesso")
    info = db.get_db_info()
    print(f"   Type: {info['type']}")
    print(f"   URL: {info['url_safe']}")
```

---

## 🗄️ Database Migrations (Alembic)

### 5. **Alembic Migrations**

Gestisci schema e dati del database:

```bash
# Upgrade all migrations
alembic upgrade head

# Downgrade
alembic downgrade -1

# Carica dati di test
alembic upgrade 20260508_add_status_match_test

# Crea nuova migrazione
alembic revision --autogenerate -m "Descrizione cambio"

# Visualizza storia
alembic history

# Stato corrente
alembic current
```

**Migrazioni disponibili:**
- `10e6bcebdb00_init_schema.py` - Schema iniziale (teams, players, matches, etc.)
- `20260508_add_status_match_and_test_data.py` - Aggiunge colonna status e dati di test
- `20260509_add_game_method.py` - Aggiunge colonna game_method

---

## 📝 Model ORM

### 6. **SQLAlchemy Models**

Accedi ai dati tramite ORM:

```python
from volleyball_scout.core.models import Team, Player, Match, MatchSet, ScoutEvent

# Teams
team = session.query(Team).filter_by(name="Attacco").first()
print(team.name)
print(team.players)  # Relazione back_populates
print(team.matches_home)

# Players
player = session.query(Player).filter_by(number=1, team_id=1).first()
print(f"{player.first_name} {player.last_name}")
print(f"Ruolo: {player.role}")
print(f"Squadra: {player.team.name}")

# Matches
match = session.query(Match).filter_by(id=1).first()
print(f"{match.home_team.name} vs {match.away_team.name}")
print(f"Stato: {match.status}")
print(f"Set: {match.sets}")
print(f"Eventi: {match.events}")

# Scout Events (DataVolley)
event = session.query(ScoutEvent).filter_by(match_id=1).first()
print(event.datavolley_code)
```

---

## 🎯 Use Cases

### Case 1: Verificare i dati nel database

**Opzione A - CLI (Fast):**
```bash
python3 check_database.py
```

**Opzione B - GUI (Visual):**
```bash
python3 check_database_ui.py
```

---

### Case 2: Aggiungere nuove squadre e giocatori

**Via UI:**
1. Avvia: `python3 volleyball_scout/run_ui.py`
2. Vai a: "👥 Team & Players"
3. Clicca: "➕ Aggiungi Squadra"
4. Compila il form e salva

**Via Script:**
```python
from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Team, Player

db = DatabaseManager()
with db.session_scope() as session:
    # Crea squadra
    team = Team(
        name="Mia Squadra",
        short_name="MS",
        category="Serie A1",
        venue="Palazzetto"
    )
    session.add(team)
    session.flush()  # Per ottenere l'ID
    
    # Crea giocatori
    for num in range(1, 15):
        player = Player(
            team_id=team.id,
            number=num,
            first_name="Giocatore",
            last_name=f"Numero {num}",
            role="Schiacciatore" if num % 2 == 0 else "Centrale"
        )
        session.add(player)
```

---

### Case 3: Esportare dati

**CLI con redirezione:**
```bash
python3 check_database.py > squadre.txt
```

**Da Script:**
```python
from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Team
import json

db = DatabaseManager()
with db.session_scope() as session:
    teams = session.query(Team).all()
    data = [
        {
            "id": t.id,
            "name": t.name,
            "players_count": len(t.players)
        }
        for t in teams
    ]
    
with open("teams.json", "w") as f:
    json.dump(data, f, indent=2)
```

---

### Case 4: Integrare nel Formation Panel

```python
from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Team, Player
from volleyball_scout.ui.formation_panel import FormationPanel

db = DatabaseManager()
with db.session_scope() as session:
    teams = session.query(Team).all()
    
    teams_list = [{"id": t.id, "name": t.name} for t in teams]
    
    players_by_team = {}
    for team in teams:
        players_by_team[team.id] = [
            {
                "id": p.id,
                "number": p.number,
                "last_name": p.last_name,
                "role": p.role,
            }
            for p in team.players
        ]
    
    # Crea panel con dati
    formation = FormationPanel(teams_list, players_by_team)
```

---

## 🗂️ File Structure

```
volley_analizer/
├── check_database.py              # 🖥️ CLI checker
├── check_database_ui.py           # 🎨 GUI checker
├── launch_database_check.py       # 🚀 Launcher GUI
├── DATABASE_CHECK_GUIDE.md        # 📖 Guida
│
├── volleyball_scout/
│   ├── run_ui.py                  # 🚀 Launcher UI
│   ├── main.py                    # Main entry point
│   │
│   ├── core/
│   │   ├── database.py            # 🗄️ DatabaseManager
│   │   ├── models.py              # 📊 ORM Models
│   │   ├── stats_engine.py        # 📈 Statistics
│   │   └── sync_engine.py         # 🔄 Sync
│   │
│   └── ui/
│       ├── app.py                 # 🏐 Main App
│       ├── main_window.py         # 👥 TeamManagementWidget, etc.
│       ├── formation_panel.py     # 🏐 Formation Setup
│       ├── scout_panel.py         # 📝 Scout
│       ├── stats_view.py          # 📈 Stats
│       └── video_player.py        # 🎥 Video
│
├── alembic/
│   └── versions/
│       ├── 10e6bcebdb00_init_schema.py
│       ├── 20260508_add_status_match_and_test_data.py
│       └── 20260509_add_game_method.py
│
└── requirements.txt               # 📦 Dependencies
```

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                   Volleyball Scout                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  UI (PyQt6)                                            │
│  ├─ app.py (Main Window)                               │
│  ├─ main_window.py (TeamManagementWidget, etc.)        │
│  ├─ formation_panel.py (Formation Setup)               │
│  └─ scout_panel.py (Scout & Video)                     │
│         ↓                                              │
│  Database Manager                                      │
│  ├─ database.py (SQLAlchemy Sessions)                  │
│  └─ Models (Team, Player, Match, etc.)                 │
│         ↓                                              │
│  SQLite / PostgreSQL                                   │
│  ├─ teams table                                        │
│  ├─ players table                                      │
│  ├─ matches table                                      │
│  ├─ match_sets table                                   │
│  ├─ scout_events table                                 │
│  └─ match_players table                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Configuration

### Environment Variables

```bash
# Database URL (default: SQLite locale)
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Per disabilitare echo queries
export SQLALCHEMY_ECHO=0
```

### Database Paths

```
SQLite (default):
  ~/.volleyball_scout/data/scout.db

PostgreSQL (cloud):
  Usa DATABASE_URL env variable (Heroku, Railway, etc.)
```

---

## 📚 Documentazione Aggiuntiva

- **Formation Panel Guide:** `volleyball_scout/ui/docs/FORMATION_PANEL.md`
- **Scout Panel Guide:** `volleyball_scout/ui/docs/SCOUT_PANEL.md`
- **Database Guide:** `DATABASE_CHECK_GUIDE.md`
- **Models Reference:** `volleyball_scout/core/models.py` (docstrings)

---

## ✅ Checklist Rapida

- [ ] Installato requirements: `pip install -r requirements.txt`
- [ ] Database inizializzato: `alembic upgrade head`
- [ ] Dati di test caricati: `alembic upgrade 20260508_add_status_match_test`
- [ ] App principale funzionante: `python3 volleyball_scout/run_ui.py`
- [ ] Database check funzionante: `python3 check_database_ui.py`

---

**Ultima modifica:** 2025-01-15
**Versione:** 1.0

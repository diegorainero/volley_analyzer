# 🏐 Database Check - Guida all'utilizzo

Questa guida spiega come verificare i dati inseriti nel database usando i due script disponibili:

1. **`check_database.py`** - Versione a riga di comando (CLI)
2. **`check_database_ui.py`** - Versione grafica (PyQt6 GUI)

---

## 📋 Requisiti

Prima di usare gli script, assicurati di avere installato le dipendenze:

```bash
pip install -r requirements.txt
```

Le dipendenze necessarie sono:
- `SQLAlchemy` (ORM database)
- `PyQt6` (solo per la versione GUI)

---

## 🖥️ Opzione 1: CLI (Command Line Interface)

### Come eseguire

```bash
cd volley_analizer
python3 check_database.py
```

### Output

Lo script mostra:

1. **Informazioni Database**
   ```
   ✅ Connessione al database riuscita!
      Database: SQLite (/home/user/.volleyball_scout/data/scout.db)
      Connesso: True
   ```

2. **Elenco Squadre**
   - ID, Nome, Categoria, Impianto, Numero Giocatori
   
3. **Giocatori per Squadra**
   - Per ogni squadra: numero, nome, cognome, ruolo, libero, capitano
   
4. **Elenco Partite**
   - ID, Casa, Trasferta, Data, Stato

### Esempio Output

```
================================================================================
  📊 SQUADRE (2)
================================================================================

ID    Nome                           Categoria            Impianto             Giocatori 
-------------------------------------------------------------------------------------
1     Attacco                        Test                 Palazzetto           7
2     Cihsosla Volley                Test                 Palazzetto           14

================================================================================
  👥 GIOCATORI PER SQUADRA
================================================================================

🔹 Attacco (7 giocatori)

  #     Nome                 Cognome              Ruolo                Libero     Capitano  
  ----                                                           -----------
  1     Marco                Rossi                Palleggiatore        -          -         
  2     Andrea               Bianchi              Schiacciatore        -          -         
  3     Luca                 Verdi                Centrale             -          -         
```

### Vantaggi
- ✅ Nessuna dipendenza grafica
- ✅ Rapido ed essenziale
- ✅ Perfetto per script o automazione
- ✅ Funziona su server senza X11

---

## 🎨 Opzione 2: GUI (Graphical User Interface)

### Come eseguire

```bash
cd volley_analizer
python3 check_database_ui.py
```

### Interfaccia

La GUI PyQt6 presenta:

1. **Header** - Stato della connessione al database
2. **3 Tab** - Una sezione per ogni tipo di dato:
   - **Squadre** - Tabella con tutte le squadre
   - **Giocatori** - Tabella con tutti i giocatori (ordinati per squadra)
   - **Partite** - Tabella con tutte le partite
3. **Pulsante Refresh** - Aggiorna i dati in tempo reale

### Funzionalità

#### Tab Squadre
| ID | Nome | Categoria | Impianto | Giocatori |
|----|------|-----------|----------|-----------|
| 1 | Attacco | Test | Palazzetto | 7 |
| 2 | Cihsosla Volley | Test | Palazzetto | 14 |

Mostra:
- ID della squadra
- Nome completo
- Categoria (es. "Serie A1", "Under 18")
- Impianto/Venue
- Numero totale di giocatori

#### Tab Giocatori
| Squadra | # | Nome | Cognome | Ruolo | Libero | Capitano |
|---------|---|------|---------|-------|--------|----------|
| Attacco | 1 | Marco | Rossi | Palleggiatore | ✓ | - |
| Attacco | 2 | Andrea | Bianchi | Schiacciatore | - | ✓ |

Mostra:
- Nome squadra a cui appartiene il giocatore
- Numero di maglia
- Nome e cognome
- Ruolo (Palleggiatore, Schiacciatore, Centrale, etc.)
- Indicatore se è libero (✓ = sì, - = no)
- Indicatore se è capitano (✓ = sì, - = no)

#### Tab Partite
| ID | Casa | Trasferta | Data | Stato |
|----|------|-----------|------|-------|
| 1 | Attacco | Cihsosla Volley | 2025-05-10 14:00 | draft |

Mostra:
- ID della partita
- Nome squadra casa
- Nome squadra trasferta
- Data e ora della partita
- Stato (draft, in_progress, completed)

### Vantaggi
- ✅ Interfaccia intuitiva
- ✅ Visualizzazione tabellare
- ✅ Colonne ridimensionabili
- ✅ Pulsante refresh per aggiornare in tempo reale
- ✅ Messaggi di errore ben visualizzati

---

## 🛠️ Integrazione con Main App

### Da Formation Panel

Se vuoi caricare i dati nel `FormationPanel`:

```python
from volleyball_scout.core.database import DatabaseManager

db = DatabaseManager()
with db.session_scope() as session:
    teams = session.query(Team).all()
    players_by_team = {}
    for team in teams:
        players = session.query(Player).filter_by(team_id=team.id).all()
        players_by_team[team.id] = [
            {
                "id": p.id,
                "number": p.number,
                "last_name": p.last_name,
                "role": p.role,
            }
            for p in players
        ]

# Crea formation panel con i dati
formation = FormationPanel(teams, players_by_team)
```

### Da TeamManagementWidget

```python
team_widget = TeamManagementWidget(db)
team_widget.load_teams()  # Carica le squadre dal DB
```

---

## 🗂️ Struttura Database

### Tabella `teams`
```sql
id          INT PRIMARY KEY
name        VARCHAR(100) NOT NULL
short_name  VARCHAR(10)
category    VARCHAR(50)     -- es. "Serie A1", "Under 18"
venue       VARCHAR(150)    -- impianto di gioco
logo        VARCHAR(250)    -- path/url logo
created_at  DATETIME
```

### Tabella `players`
```sql
id          INT PRIMARY KEY
team_id     INT FOREIGN KEY -> teams.id
number      INT NOT NULL
first_name  VARCHAR(50)
last_name   VARCHAR(50) NOT NULL
role        VARCHAR(30)     -- Palleggiatore, Schiacciatore, etc.
is_libero   BOOLEAN
captain     BOOLEAN
birth_date  DATETIME
photo       VARCHAR(250)
```

### Tabella `matches`
```sql
id          INT PRIMARY KEY
home_team_id    INT FOREIGN KEY -> teams.id
away_team_id    INT FOREIGN KEY -> teams.id
date        DATETIME NOT NULL
venue       VARCHAR(150)
competition VARCHAR(100)
video_path  VARCHAR(500)
status      VARCHAR(20)     -- draft, in_progress, completed
```

---

## 📍 Posizione Database

### SQLite (Default)
```
~/.volleyball_scout/data/scout.db
```

### PostgreSQL (Cloud)
Se è settata la variabile di ambiente `DATABASE_URL`, viene usato PostgreSQL (es. Heroku, Railway).

Per verificare quale database viene usato:

**CLI:**
```
Database: SQLite (/home/user/.volleyball_scout/data/scout.db)
```

**GUI:**
```
✅ Database connesso: SQLite (/home/user/.volleyball_scout/data/scout.db)
```

---

## 🆘 Troubleshooting

### Errore: "ModuleNotFoundError: No module named 'sqlalchemy'"

Installa le dipendenze:
```bash
pip install -r requirements.txt
```

### Errore: "❌ Errore: Impossibile connettere il database"

Verifiche:
1. Il file `scout.db` esiste in `~/.volleyball_scout/data/`?
2. Se usi PostgreSQL, è settata la variabile `DATABASE_URL`?
3. Le migrazioni Alembic sono state applicate?

```bash
# Applica migrazioni
cd volley_analizer
alembic upgrade head
```

### Nessun dato nel database

Il database è vuoto. Puoi:

1. **Aggiungere dati tramite UI:**
   - Avvia l'app principale: `python3 run_ui.py`
   - Vai nel tab "Team & Players"
   - Aggiungi squadre e giocatori

2. **Aggiungere dati via script:**
   - Usa gli script in `scripts/`
   - O crea una migrazione Alembic

3. **Carica i dati di test:**
   - La migrazione `20260508_add_status_match_and_test_data.py` inserisce dati di test
   ```bash
   alembic upgrade 20260508_add_status_match_test
   ```

---

## 💡 Tips

### Aggiornare i dati in tempo reale

Nella GUI, clicca il pulsante **🔄 Aggiorna Dati** per ricaricare da database.

### Esportare i dati

Dalla CLI, puoi redirigere l'output:
```bash
python3 check_database.py > database_dump.txt
```

### Integrare nel tuo script

```python
from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Team, Player

db = DatabaseManager()
session = db.get_session()

# Query personnalizzata
all_teams = session.query(Team).all()
for team in all_teams:
    print(f"{team.name}: {len(team.players)} giocatori")

session.close()
```

---

## 📚 Riferimenti

- **Database Manager:** `volleyball_scout/core/database.py`
- **Models:** `volleyball_scout/core/models.py`
- **Migrazioni:** `alembic/versions/`
- **UI App:** `volleyball_scout/ui/app.py`

---

**Ultima modifica:** 2025-01-15

# 🏐 Volleyball Scout

App professionale di scouting pallavolo con sincronizzazione video e export DataVolley (.dvw).  
Compatibile con **DataVolley 4 / DataProject**.

---

## Stack tecnologico

| Layer | Tecnologia | Motivo |
|---|---|---|
| UI | **PyQt6** | Cross-platform nativo (Win/Mac/Linux), professionale |
| Database locale | **SQLite** via SQLAlchemy | Zero config, file singolo |
| Database cloud | **PostgreSQL** via SQLAlchemy | Stessa ORM, cambio URL |
| Video | **python-vlc** | Player VLC embedded, frame-accurate |
| Export | Parser custom | Formato .dvw DataVolley 4 |
| Packaging | **PyInstaller** | .exe / .app distribuibile |

---

## Struttura progetto

```
volleyball_scout/
├── main.py                    # Entry point
├── requirements.txt
├── .env                       # DATABASE_URL (opzionale per cloud)
│
├── core/
│   ├── models.py              # ORM: Team, Player, Match, ScoutEvent
│   ├── database.py            # Engine SQLite/PostgreSQL
│   ├── sync_engine.py         # Sincronizzazione video↔eventi
│   └── stats_engine.py        # Calcolo statistiche DataVolley
│
├── ui/
│   ├── main_window.py         # Finestra principale PyQt6
│   ├── scout_panel.py         # Tastiera eventi live
│   ├── video_player.py        # Player VLC embedded
│   └── stats_view.py          # Dashboard statistiche
│
├── exporters/
│   └── datavolley.py          # Export/Import .dvw
│
└── utils/
    └── timestamp.py           # Utility timestamp video
```

---

## Installazione

### Setup Automatico (Consigliato)
```bash
# 1. Clona / scarica il progetto
cd volleyball_scout

# 2. Crea ambiente virtuale
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Setup automatico (installa dipendenze + migrazioni DB)
python setup.py dev_setup

# 4. Installa VLC (se necessario per player)
#    Windows/Mac: scarica da https://www.videolan.org/vlc/
#    Linux: sudo apt install vlc

# 5. Avvia
python main.py
```

### Setup Manuale
```bash
python -m venv venv
source venv/bin/activate

---

## Configurazione database cloud

Crea un file `.env` nella root del progetto:

```env
# Esempio con Supabase (PostgreSQL gratuito)
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/volleyball_scout

# Esempio con Railway
DATABASE_URL=postgresql://postgres:xxx@containers-us-west-1.railway.app:6543/railway
```

Se `.env` non è presente → usa SQLite locale in `~/.volleyball_scout/data/scout.db`

---

## Formato DataVolley (.dvw)

### Codici Skill
| Codice | Azione |
|---|---|
| S | Battuta (Serve) |
| R | Ricezione |
| E | Alzata (Set) |
| A | Attacco |
| B | Muro (Block) |
| D | Difesa (Dig) |
| F | Freeball |

### Codici Valutazione
| Codice | Significato |
|---|---|
| # | Perfetto / Ace / Punto diretto |
| + | Positivo |
| ! | Sovramano |
| - | Negativo |
| = | Errore |
| / | Metà |

### Zone campo (1-9)
```
 ┌───┬───┬───┐
 │ 7 │ 8 │ 9 │  ← Zona di attacco
 ├───┼───┼───┤
 │ 4 │ 5 │ 6 │  ← Zona centrale
 ├───┼───┼───┤
 │ 1 │ 2 │ 3 │  ← Zona difensiva
 └───┴───┴───┘
```

---

## Sync Video

Il motore di sincronizzazione funziona così:

1. **Calibrazione**: Al fischio d'inizio, premi il pulsante "Calibra" → salva il timestamp video
2. **Inserimento eventi**: Ogni evento viene associato alla posizione corrente del video
3. **Revisione**: Clicca su un evento per tornare al video 3 secondi prima
4. **Offset**: Se carichi una partita già registrata, imposta l'offset manualmente

---

## Export DVW

```python
from exporters.datavolley import DataVolleyExporter
from core.database import get_db

db = get_db()
with db.get_session() as session:
    exporter = DataVolleyExporter(session)
    path = exporter.export(match_id=1, output_path="partita.dvw")
    print(f"Esportato: {path}")
```

---

## Roadmap

- [x] Modelli DB (Team, Player, Match, ScoutEvent)
- [x] Engine SQLite → PostgreSQL
- [x] Sync engine video↔timestamp  
- [x] Export .dvw DataVolley 4
- [x] Calcolo statistiche
- [x] UI PyQt6 - Dashboard, Gestione Squadre, Match Management
- [x] Roster Setup (scelta convocati)
- [x] Formation Panel (selezione titolari e libero)
- [x] Database SQLite con ORM SQLAlchemy
- [x] Migrazioni Alembic (campo `is_starter` aggiunto)
- [x] Setup automatico con `python setup.py dev_setup`
- [ ] UI PyQt6 - Scout panel tastiera (in progress)
- [ ] UI PyQt6 - Player VLC embedded
- [ ] UI PyQt6 - Dashboard statistiche
- [ ] Test automatici
- [ ] Packaging PyInstaller
- [ ] Sync cloud multi-utente

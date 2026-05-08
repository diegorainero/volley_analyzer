# 🏐 Volleyball Scout - Project Structure

## Project Layout

```
volley_analizer/
├── volleyball_scout/
│   ├── __init__.py                 # Package root
│   ├── main.py                     # CLI entry point
│   ├── check_system.py             # System health check
│   │
│   ├── core/                       # Core business logic
│   │   ├── __init__.py
│   │   ├── database.py             # DatabaseManager, get_db()
│   │   ├── models.py               # SQLAlchemy models (Match, Player, Team, etc)
│   │   ├── stats_engine.py         # StatsEngine
│   │   └── sync_engine.py          # SyncEngine
│   │
│   ├── ui/                         # PyQt6 User Interface
│   │   ├── __init__.py
│   │   ├── __main__.py             # UI entry point
│   │   ├── app.py                  # VolleyballScoutApp (Main window)
│   │   ├── main_window.py          # Entry point wrapper
│   │   ├── matches_grid.py         # MatchesGridWidget
│   │   ├── scout_panel.py          # ScoutPanel
│   │   ├── formation_panel.py      # FormationPanel
│   │   ├── stats_view.py           # StatsView
│   │   ├── video_player.py         # VideoPlayer
│   │   │
│   │   ├── drafts/                 # Draft management
│   │   │   ├── __init__.py
│   │   │   ├── draft_widget.py     # DraftListWidget
│   │   │   └── draft_manager.py    # Draft session management
│   │   │
│   │   └── README.md               # UI documentation
│   │
│   ├── exporters/                  # Export formats
│   │   ├── __init__.py
│   │   └── datavolley.py           # DataVolleyExporter
│   │
│   └── README.md                   # Scout module docs
│
└── README.md                        # Main project README
```

## How to Run

### 1. **Check System Health**
```bash
cd volley_analizer
venv/bin/python -m volleyball_scout.check_system
```
This verifies all modules are working correctly.

### 2. **Launch UI**
```bash
cd volley_analizer
venv/bin/python -m volleyball_scout.ui
```
This starts the PyQt6 application with the Dashboard.

### 3. **Run CLI Demo**
```bash
cd volley_analizer
venv/bin/python -m volleyball_scout.main
```
This demonstrates basic database operations.

## Core Components

### 1. **Database Layer** (`core/database.py`)
- **DatabaseManager**: Handles SQLite (local) and PostgreSQL (cloud)
- **get_db()**: Singleton function to get the database manager
- **Features**:
  - Automatic URL detection (env var or local SQLite)
  - Connection pooling
  - Session management

### 2. **Data Models** (`core/models.py`)
SQLAlchemy ORM models:
- `Team`: Team information
- `Player`: Players with jersey numbers
- `Match`: Match metadata
- `MatchPlayer`: Player roster for a specific match
- `ScoutEvent`: Individual scouting events (skills, zones, evaluations)
- `MatchDraft`: In-progress scouting sessions

### 3. **UI Components** (`ui/`)
- **VolleyballScoutApp**: Main window
- **DashboardView**: Grid of available matches and draft sessions
- **MatchesGridWidget**: Visual match list
- **FormationPanel**: Display and edit court formations
- **ScoutPanel**: Real-time scouting interface
- **DraftListWidget**: Resume saved draft sessions
- **StatsView**: Match statistics view
- **VideoPlayer**: Synchronized video playback

### 4. **Engines** (`core/`)
- **StatsEngine**: Calculates match statistics
- **SyncEngine**: Synchronizes data between local and cloud

### 5. **Exporters** (`exporters/`)
- **DataVolleyExporter**: Export to DataVolley format

## Key Features

✅ **Database Management**
- Local SQLite for development
- PostgreSQL for cloud deployment
- SQLAlchemy ORM for clean data layer

✅ **Formation Management**
- Visual court representation
- Rotation logic (1→6→5→4→3→2)
- Libero tracking
- Automatic game method detection

✅ **Scouting Interface**
- Real-time event logging
- Video sync
- Formation editing
- Draft session persistence

✅ **Export Capabilities**
- DataVolley format support
- Statistics export

## Import Examples

```python
# Core imports
from volleyball_scout.core.database import DatabaseManager, get_db
from volleyball_scout.core.models import Match, Player, Team, ScoutEvent
from volleyball_scout.core.stats_engine import StatsEngine
from volleyball_scout.core.sync_engine import SyncEngine

# UI imports
from volleyball_scout.ui.app import VolleyballScoutApp
from volleyball_scout.ui.formation_panel import FormationPanel
from volleyball_scout.ui.scout_panel import ScoutPanel
from volleyball_scout.ui.drafts.draft_widget import DraftListWidget

# Exporters
from volleyball_scout.exporters.datavolley import DataVolleyExporter
```

## Development

### Add New Components
1. Create the module in the appropriate subdirectory
2. Add imports to the `__init__.py` of the parent package
3. Test imports with the health check

### Modify Database Models
1. Edit `core/models.py`
2. Create a migration with Alembic if schema changes
3. Test with the health check

### Add New UI Panels
1. Create a new file in `ui/`
2. Define your widget class
3. Import in `app.py` and integrate with the main window

## Troubleshooting

**ModuleNotFoundError**: Always run with `-m` flag:
```bash
venv/bin/python -m volleyball_scout.ui
# NOT: venv/bin/python volleyball_scout/ui/main_window.py
```

**Database Connection Error**: Check `.volleyball_scout/data/scout.db` permissions or `DATABASE_URL` env var.

**Import Errors**: Run health check to diagnose missing modules:
```bash
venv/bin/python -m volleyball_scout.check_system
```

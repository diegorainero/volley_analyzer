# 🏐 Volleyball Scout - Integrated UI Guide

## Overview

The Volleyball Scout application now features a **fully integrated graphical interface** with menu-based navigation. When you launch "Volleyball Scout" from the main menu, you get a single window with all components connected via a sidebar navigation menu.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│          🏐 VOLLEYBALL SCOUT - Formation & Analysis             │
├──────────────────┬──────────────────────────────────────────────┤
│                  │                                              │
│  NAVIGATION      │          CONTENT AREA (Stacked Widget)       │
│  MENU (Left)     │                                              │
│  ────────────    │  ┌────────────────────────────────────────┐  │
│  📊 Dashboard    │  │ [Dashboard, Teams, Roster, Formation,  │  │
│  👥 Teams        │  │  Scout & Video, Statistics]            │  │
│  📋 Roster       │  │ (Switch based on menu selection)       │  │
│  🏐 Formation    │  └────────────────────────────────────────┘  │
│  📝 Scout        │                                              │
│  📈 Statistics   │                                              │
│                  │                                              │
│  ────────────    │                                              │
│  v1.0 - Scout Pro│                                              │
└──────────────────┴──────────────────────────────────────────────┘
```

## Launching the Application

### From Main Menu
```bash
cd volley_analizer
python3 main.py
# Select option 2: Volleyball Scout
```

### Directly
```bash
cd volley_analizer
python3 -m volleyball_scout.ui.app
```

## Sections Overview

### 1. 📊 Dashboard
**Location:** First section (default on startup)

Shows:
- **Left Panel:** Grid of all matches with color-coded status
  - 🔲 **Bozza (Draft)** - Light gray
  - ⏳ **In Corso (In Progress)** - Light yellow
  - ✅ **Completato (Completed)** - Light green
- **Right Panel:** List of draft sessions in progress

**Actions:**
- Click on a match card to select it
- Click on a draft session to resume scouting
- Auto-refreshes when section is visited

---

### 2. 👥 Team & Players
**Location:** Second section

Comprehensive team management interface with:

#### Team Management (Left Panel)
- View all teams
- Add new teams
- Edit team information
- Upload team logo
- Delete teams

#### Player Management (Right Panel)
- View players for selected team
- Add new players
- Edit player details (number, role, name)
- Upload player photo
- Delete players
- Assign players to teams

**Key Features:**
- Roles: Palleggiatore, Schiacciatore, Opposto, Centrale, Libero, Universale
- Multi-team support
- Photo/Logo management

---

### 3. 📋 Roster Setup
**Location:** Third section

Setup the roster for a match:

**Workflow:**
1. Select a match
2. Select home team
3. Choose players from the roster (multi-select)
4. Confirm to proceed to Formation Setup

**Actions:**
- Back button to return to previous step
- Next button to continue to Formation

---

### 4. 🏐 Formation Setup
**Location:** Fourth section

Advanced formation panel with drag-and-drop:

**Features:**
- **Player Circles** (top) - Draggable players
- **6 Position Slots** - For starting lineup (formation positions)
- **Libero Slot** - Special slot for the libero player
- **Game Method Detection** - P-S-C or P-C-S (auto-detect)
- **Rotation Support** - Rotate formation on court

**Workflow:**
1. Select team
2. Drag players to formation slots
3. Assign libero
4. Detect game method (or set manually)
5. Confirm formation to save to database

**Validation:**
- ✅ Requires exactly 6 starters
- ✅ Requires exactly 1 libero
- ✅ No duplicate assignments
- ✅ Saves to `match_players` table (is_starter, is_libero fields)

---

### 5. 📝 Scout & Video
**Location:** Fifth section

Split panel with:

**Left Panel - Scout Panel:**
- Event input keyboard (work in progress)
- Event type selection buttons
- Real-time event tracking

**Right Panel - Video Player:**
- VLC embedded player (placeholder)
- Video sync controls
- Frame-accurate playback

**Integration:**
- Video timestamp sync with events
- Auto-save events to database
- Draft management (auto-save progress)

---

### 6. 📈 Statistics
**Location:** Sixth section

Dashboard with:
- Match statistics
- Player statistics
- Team performance metrics
- DataVolley export button

**Database Tools:**
- Apply Alembic migrations button
- Check database schema status

---

## Navigation Menu Features

### Sections
The left sidebar shows all available sections:

```
🏐 VOLLEYBALL SCOUT
─────────────────────
📊 Dashboard
👥 Team & Players
📋 Roster Setup
🏐 Formation Setup
📝 Scout & Video
📈 Statistics
─────────────────────
v1.0 - Scout Pro
```

### Visual Feedback
- **Inactive button:** Dark blue background (#2C3E50)
- **Hover state:** Slightly lighter blue (#34495E)
- **Active button:** Bright blue (#0066CC)

### Keyboard Navigation
- Tab through sections
- Enter to select
- Arrow keys to navigate within content

---

## Data Flow

```
Main Menu (main.py)
    ↓
Volleyball Scout Selected
    ↓
VolleyballScoutApp Initializes
    ↓
Database Connection
    ↓
Dashboard View (default)
    ↓
User Selects Section via Menu
    ↓
Content Stack Updates
    ↓
Respective Widget Displayed
    ↓
Data Operations (CRUD)
    ↓
Database Updates
```

---

## Database Integration

All sections interact with the database:

### Models Used
- `Team` - Team information
- `Player` - Player details
- `Match` - Match schedule
- `MatchPlayer` - Match roster (with is_starter, is_libero flags)
- `ScoutEvent` - Event tracking during match
- `Draft` - Draft session management

### Session Management
- Uses SQLAlchemy ORM
- Context manager for safe sessions
- Automatic connection pooling
- Supports SQLite (local) or PostgreSQL (cloud)

---

## Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# For cloud database
DATABASE_URL=postgresql://user:password@db.example.com/volleyball_scout

# For local SQLite (default)
# No configuration needed - auto-uses ~/.volleyball_scout/data/scout.db
```

### Database File Locations
- **SQLite:** `~/.volleyball_scout/data/scout.db`
- **PostgreSQL:** Set via `DATABASE_URL` env variable

---

## Troubleshooting

### Database Connection Error
```
❌ Errore connessione database
```

**Solutions:**
1. Check database file exists: `ls ~/.volleyball_scout/data/`
2. Verify migrations applied: `python3 -m alembic upgrade head`
3. Check PostgreSQL connection if using cloud

### Missing PyQt6
```
ModuleNotFoundError: No module named 'PyQt6'
```

**Solution:**
```bash
pip install PyQt6
```

### Widget Not Showing
- Check console output for errors
- Verify database queries return data
- Ensure database schema is up to date

---

## Development Notes

### Adding a New Section

1. Create the widget in `ui/` directory
2. Import in `app.py`
3. Add to `_setup_sections()` method
4. Add to navigation menu buttons
5. Update `section_map` in `_on_section_selected()`

Example:
```python
# In app.py _setup_sections()
self.new_widget = NewWidget(self.db)
self.content_stack.addWidget(self.new_widget)  # Index 6

# In __init__ sections list
("📌 New Section", "new_section"),

# In _on_section_selected()
"new_section": 6,
```

### Styling

The app uses:
- **Qt Stylesheets (CSS-like)**
- **Fusion Style** (set in main())
- **Inline styles** for dynamic elements

To customize:
- Edit `NavigationMenu` button_style
- Modify color hex codes
- Update fonts in QFont() calls

### Testing

Run individual widgets:
```bash
# Test Formation Panel
python3 tests/test_formation_panel_ui.py

# Test Dashboard
python3 -c "
from volleyball_scout.ui.app import DashboardView
from volleyball_scout.core.database import DatabaseManager
db = DatabaseManager()
# ... test code
"
```

---

## Keyboard Shortcuts (Future)

| Shortcut | Action |
|----------|--------|
| `Ctrl+D` | Go to Dashboard |
| `Ctrl+T` | Go to Teams |
| `Ctrl+F` | Go to Formation |
| `Ctrl+S` | Go to Scout |
| `Ctrl+Z` | Undo last action |
| `Ctrl+Q` | Quit application |

*(Shortcuts not yet implemented - contribute via PR!)*

---

## Related Documentation

- [Formation Panel Guide](../formation_panel.py)
- [Scout Panel Guide](../scout_panel.py)
- [Matches Grid Guide](../matches_grid.py)
- [Draft System](../drafts/draft_widget.py)
- [Database Models](../../core/models.py)
- [Statistics Engine](../../core/stats_engine.py)

---

## Version History

**v1.0 - Initial Release**
- ✅ Integrated navigation menu
- ✅ Dashboard with matches grid and drafts
- ✅ Team & Players management
- ✅ Roster setup
- ✅ Formation panel with drag-and-drop
- ✅ Scout & Video player placeholders
- ✅ Statistics view

**Future Features**
- Video sync with event timestamps
- Advanced scouting keyboard
- Player statistics dashboard
- Export to DataVolley (.dvw)
- Multi-user sync

---

## Support

For issues or suggestions:
1. Check the console output for error messages
2. Review database migrations: `alembic history`
3. Check database integrity: `sqlite3 ~/.volleyball_scout/data/scout.db ".schema"`
4. Report issues with full traceback

---

**Happy Scouting! 🏐**

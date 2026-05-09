# Volleyball Scout UI - PyQt6

## Quick Start

### Launch the Application

```bash
# From project root
python3 volleyball_scout/ui/app.py
```

## Components

### 1. **MatchesGridWidget** 
Displays all matches in a grid with color-coded status:
- **🔲 Bozza (Draft)** → Gray (#E8E8E8)
- **⏳ In Corso (In Progress)** → Yellow (#FFFACD)
- **✅ Completato (Completed)** → Green (#C8E6C9)

Each card shows:
- Date (DD/MM/YYYY)
- Home Team vs Away Team
- Current status with emoji

Click on any match to open scout.

**Location:** `volleyball_scout/ui/matches_grid.py`

### 2. **DraftListWidget**
Manages draft sessions that are in progress.

Features:
- Auto-saves sessions
- Resume from where you left off
- Delete drafts

**Location:** `volleyball_scout/ui/drafts/`

### 3. **FormationPanel**
Advanced formation setup with drag-and-drop.

Features:
- Player circles (blue) at top
- 6 position slots for starting lineup
- Separate libero slots with available players
- Rotation support
- Game method detection (P-S-C or P-C-S)

**Location:** `volleyball_scout/ui/formation_panel.py`

## Architecture

```
┌─────────────────────────────────────────┐
│    VolleyballScoutApp (QMainWindow)     │
└──────────────┬──────────────────────────┘
               │
               └─► DashboardView (QWidget)
                   ├─► MatchesGridWidget (Left Panel)
                   │   ├─► MatchCardWidget (repeating)
                   │   └─► Scroll Area with Grid
                   │
                   └─► DraftListWidget (Right Panel)
                       └─► Draft Sessions List
```

## Key Features

### Dashboard Integration
- **Left Side:** All matches in grid format with status colors
- **Right Side:** Draft sessions for resuming scouting

### Match Card Colors
| Status | Color | Hex |
|--------|-------|-----|
| Draft | Light Gray | #E8E8E8 |
| In Progress | Light Yellow | #FFFACD |
| Completed | Light Green | #C8E6C9 |

### Responsive Design
- 4-column grid layout (adjusts with window size)
- Scrollable area for many matches
- Hover effects on cards

## Usage Examples

### Use MatchesGridWidget standalone

```python
from volleyball_scout.ui import MatchesGridWidget
from volleyball_scout.core.db_manager import DatabaseManager

db = DatabaseManager()
matches_widget = MatchesGridWidget(db)
matches_widget.match_selected.connect(on_match_selected)
```

### Use FormationPanel

```python
from volleyball_scout.ui import FormationPanel

formation = FormationPanel(teams, players_by_team)
formation.formation_confirmed.connect(on_formation_confirmed)
```

## Development Notes

- All widgets are independent and can be used separately
- Database session handling is automatic
- Signals are used for communication between components
- Styling is CSS-based (Qt stylesheets)

## Requirements

- PyQt6
- SQLAlchemy
- volleyball_scout.core (database models and manager)

## Testing

Run the dashboard:
```bash
python3 volleyball_scout/ui/app.py
```

Test formation panel:
```bash
python3 tests/test_formation_panel_ui.py
```

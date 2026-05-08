# 🏐 Volleyball Scout - UI Architecture

## System Architecture Diagram

```
╔════════════════════════════════════════════════════════════════════════╗
║                         MAIN APPLICATION WINDOW                       ║
║                  🏐 VOLLEYBALL SCOUT - Formation & Analysis            ║
╠═══════════════════════╦══════════════════════════════════════════════╣
║   NAVIGATION MENU     ║        CONTENT AREA (QStackedWidget)         ║
║   (QWidget - Left)    ║                                              ║
║   Width: 220px        ║  Shows one of 6 sections at a time:          ║
║                       ║                                              ║
║  ┌─────────────────┐  ║  ┌──────────────────────────────────────┐  ║
║  │ 🏐 VOLLEYBALL   │  ║  │ [ACTIVE SECTION CONTENT]             │  ║
║  │    SCOUT        │  ║  │                                      │  ║
║  ├─────────────────┤  ║  │ Index 0: Dashboard                   │  ║
║  │ 📊 Dashboard    │  ║  │ Index 1: Team & Players              │  ║
║  │ 👥 Team         │  ║  │ Index 2: Roster Setup                │  ║
║  │ 📋 Roster       │  ║  │ Index 3: Formation Setup             │  ║
║  │ 🏐 Formation    │  ║  │ Index 4: Scout & Video               │  ║
║  │ 📝 Scout        │  ║  │ Index 5: Statistics                  │  ║
║  │ 📈 Statistics   │  ║  │                                      │  ║
║  ├─────────────────┤  ║  └──────────────────────────────────────┘  ║
║  │ v1.0            │  ║                                              ║
║  │ Scout Pro       │  ║                                              ║
║  └─────────────────┘  ║                                              ║
╚═══════════════════════╩══════════════════════════════════════════════╝
```

---

## Component Hierarchy

```
VolleyballScoutApp (QMainWindow)
├── setCentralWidget(main_widget)
│
└── main_widget (QWidget)
    ├── main_layout (QHBoxLayout)
    │
    ├── NavigationMenu (QWidget) [Left]
    │   ├── Layout (QVBoxLayout)
    │   ├── Title Label
    │   ├── Separator Label
    │   ├── Section Buttons
    │   │   ├── QPushButton "📊 Dashboard"
    │   │   ├── QPushButton "👥 Team & Players"
    │   │   ├── QPushButton "📋 Roster Setup"
    │   │   ├── QPushButton "🏐 Formation Setup"
    │   │   ├── QPushButton "📝 Scout & Video"
    │   │   └── QPushButton "📈 Statistics"
    │   ├── Spacer (addStretch)
    │   └── Footer Label
    │
    └── content_stack (QStackedWidget) [Right - Main Content]
        ├── [Index 0] DashboardView
        │   ├── MatchesGridWidget (Left)
        │   │   └── MatchCardWidget (repeating)
        │   └── DraftListWidget (Right)
        │
        ├── [Index 1] TeamManagementWidget
        │   ├── Team List (Left)
        │   ├── Team Form (Right)
        │   ├── Player List (Left)
        │   └── Player Form (Right)
        │
        ├── [Index 2] RosterSetupWidget
        │   ├── Match/Team Info
        │   ├── Available Players
        │   ├── Selected Players
        │   └── Next/Back Buttons
        │
        ├── [Index 3] FormationPanel
        │   ├── Team Selection
        │   ├── Available Players (draggable)
        │   ├── Formation Slots (6 positions)
        │   ├── Libero Slot
        │   ├── Game Method Selection
        │   ├── Rotation Controls
        │   └── Confirm Button
        │
        ├── [Index 4] Scout & Video Container
        │   ├── ScoutPanel (Left)
        │   │   ├── Event Buttons
        │   │   ├── Event Log
        │   │   └── Team Selection
        │   └── VideoPlayer (Right)
        │       ├── Video Display
        │       ├── Play/Pause/Stop
        │       └── Timeline Slider
        │
        └── [Index 5] StatsView
            ├── Match Stats
            ├── Player Stats
            ├── Team Performance
            └── Export Button
```

---

## Data Flow Diagram

```
User Interaction
    │
    ├─ Click Navigation Button
    │   ├─> _on_section_selected(section_id)
    │   ├─> content_stack.setCurrentIndex(index)
    │   ├─> nav_menu.highlight_section(section_id)
    │   └─> [If Dashboard] dashboard.refresh()
    │
    ├─ Interact with Content
    │   ├─> Widget processes user action
    │   ├─> Query/Update database via DatabaseManager
    │   ├─> Emit signals (match_selected, draft_resumed, etc.)
    │   └─> UI updates based on response
    │
    └─ Close Application
        ├─> closeEvent()
        └─> db.close()
```

---

## Database Integration Points

```
VolleyballScoutApp
├── __init__()
│   └─> DatabaseManager() - Initialize connection
│
├── _setup_sections()
│   ├─> DashboardView(db_manager)
│   ├─> TeamManagementWidget(db_manager)
│   ├─> RosterSetupWidget(db_manager)
│   ├─> FormationPanel(db_manager)
│   └─> StatsView()
│
├── Each Widget
│   ├─> Query data: db.session_scope() as session
│   ├─> Create: session.add(object) + session.commit()
│   ├─> Read: session.query(Model).filter(...).all()
│   ├─> Update: object.field = value + session.commit()
│   └─> Delete: session.delete(object) + session.commit()
│
└── closeEvent()
    └─> db.close() - Clean shutdown
```

---

## Signal/Slot Connections

```
NavigationMenu
    └─ section_selected(str)
       └─> VolleyballScoutApp._on_section_selected(section_id)
           └─> content_stack.setCurrentIndex()
               └─> Displays corresponding widget

DashboardView
    ├─ MatchesGridWidget
    │  └─ match_selected(int)
    │     └─> [Could trigger formation setup]
    │
    └─ DraftListWidget
       └─ draft_resumed(int)
          └─ [Could load match into scout panel]

FormationPanel
    └─ formation_confirmed(dict)
       └─ [Could trigger match start]

RosterSetupWidget
    ├─ next_requested()
    │  └─ [Could trigger formation setup]
    │
    └─ back_requested()
       └─ [Go back to previous step]
```

---

## Section Details

### Section 0: Dashboard

```
DashboardView
├── Left Panel (1:1 ratio)
│   ├── Header: "📋 Match Disponibili"
│   └── MatchesGridWidget
│       ├── ScrollArea
│       └── GridLayout
│           ├── MatchCardWidget (4-column grid)
│           │   ├── Date label
│           │   ├── Teams label
│           │   └── Status label (colored)
│           └── ...
│
└── Right Panel (1:1 ratio)
    ├── Header: "📝 Sessioni in Bozza"
    └── DraftListWidget
        └── QListWidget with drafts
```

**Status Colors:**
- Draft: #E8E8E8 (Light Gray)
- In Progress: #FFFACD (Light Yellow)
- Completed: #C8E6C9 (Light Green)

---

### Section 1: Team & Players Management

```
TeamManagementWidget
├── Header
│   ├── "Gestione Squadre" title
│   └── "Aggiungi Squadra" button
│
└── Content (QGroupBox)
    ├── Left Panel: Teams List
    │   └── QListWidget
    │       └── Team items (clickable)
    │
    └── Right Panel: Team Form + Players
        ├── Team Information Section
        │   ├── Name input
        │   ├── Logo upload
        │   └── Save/Delete buttons
        │
        └── Players Section
            ├── Players List (QListWidget)
            └── Player Form
                ├── Name, Number, Role inputs
                ├── Photo upload
                └── Save/Delete buttons
```

**Roles Available:**
- Palleggiatore (Setter)
- Schiacciatore (Hitter)
- Opposto (Opposite)
- Centrale (Middle Blocker)
- Libero (Libero)
- Universale (Universal)

---

### Section 2: Roster Setup

```
RosterSetupWidget
├── Header
│   ├── "Preparazione Roster" title
│   └── Instructions
│
├── Content
│   ├── Team Info Section
│   │   └── Team name label
│   │
│   ├── Players Section
│   │   ├── Header: "Giocatrici Disponibili"
│   │   └── QListWidget with MultiSelection
│   │
│   └── Buttons
│       ├── "Indietro" (Back)
│       └── "Avanti" (Next)
│
└── Workflow
    1. Load match
    2. Select team
    3. Load available players
    4. Multi-select players
    5. Save selection
    6. Go to Formation Setup
```

---

### Section 3: Formation Setup

```
FormationPanel
├── Team Selection
│   └── Dropdown to select team
│
├── Players Display
│   ├── Available Players (top)
│   │   └── PlayerButton (draggable circles)
│   │
│   ├── Formation Area (center)
│   │   ├── FormationSlot [1..6]
│   │   │   └── Accepts: 1 player from draggable pool
│   │   │
│   │   └── LiberoSlot
│   │       └── Accepts: 1 libero player
│   │
│   └── Rotation Controls
│       └── Rotate formation buttons
│
├── Game Method Section
│   ├── P-S-C button
│   ├── P-C-S button
│   └── Auto-detect button
│
└── Confirm & Rotation
    ├── "Conferma Formazione" button
    └── "Ruota" button
```

**Validation:**
- ✅ Exactly 6 starters in slots
- ✅ Exactly 1 libero in libero slot
- ✅ No duplicate player assignments

---

### Section 4: Scout & Video

```
Scout & Video Container
├── Left Panel: ScoutPanel (1:2 ratio)
│   ├── Header
│   ├── Event Buttons
│   │   ├── "Attacco" (Attack)
│   │   ├── "Muro" (Block)
│   │   ├── "Battuta" (Serve)
│   │   ├── "Ricezione" (Reception)
│   │   ├── "Alzata" (Set)
│   │   └── "Difesa" (Defense)
│   │
│   ├── Event Log
│   └── Team Selection
│
└── Right Panel: VideoPlayer (2:2 ratio)
    ├── Video Display Area
    ├── Controls
    │   ├── Play button
    │   ├── Pause button
    │   └── Stop button
    │
    └── Timeline Slider
```

---

### Section 5: Statistics

```
StatsView
├── Title: "Stats View - Dashboard statistiche"
│
├── Match Statistics
│   ├── Summary stats
│   ├── Point progression
│   └── Set breakdown
│
├── Player Statistics
│   ├── Per-player breakdown
│   └── Comparative analysis
│
├── Database Tools
│   └── "Applica Migrazione DB (Alembic)" button
│
└── Export
    └── Export to DataVolley (.dvw)
```

---

## Color Scheme

```
Primary Colors:
  Dark Blue      #2C3E50  (Navigation background, button base)
  Light Blue     #34495E  (Hover state)
  Accent Blue    #0066CC  (Active state, highlights)
  Light Blue     #0052A3  (Hover on active)

Secondary Colors:
  Light Gray     #ECF0F1  (Navigation panel background)
  Gray           #95A5A6  (Footer text)
  Separator      #BDC3C7  (Lines, separators)
  White          #FFFFFF  (Main content background)

Status Colors:
  Draft          #E8E8E8  (Light gray)
  In Progress    #FFFACD  (Light yellow)
  Completed      #C8E6C9  (Light green)
  Error          #FF6B6B  (Error red)
  Success        #51CF66  (Success green)
```

---

## Typography

```
Title (App Name)
  Font: Arial
  Weight: Bold
  Size: 12px
  Color: #2C3E50

Section Titles
  Font: Arial
  Weight: Bold
  Size: 11px (buttons)
  Color: White (on dark background)

Body Text
  Font: Default (system)
  Size: 10-11px
  Color: #2C3E50

Monospace (debugging)
  Font: Courier/Monospace
  Size: 10px
  Color: Console output
```

---

## Responsive Design

```
Window Size: 1800x1000 (default)
  ├─ Navigation Menu: 220px width (fixed)
  └─ Content Area: Remaining width (flexible)

Content Stack:
  ├─ Scrollable areas expand/contract
  ├─ Widgets use layouts (not fixed sizes)
  └─ Proportional splitting with layout stretching

Minimum Window Size:
  ├─ Width: 1000px
  ├─ Height: 600px
  └─ Below these, UI may be cramped
```

---

## State Management

```
VolleyballScoutApp State:
  ├─ current_section: str (dashboard, teams, roster, etc.)
  ├─ db: DatabaseManager instance
  ├─ content_stack: Currently active widget index
  └─ nav_menu: Button highlight state

Widget-level State:
  ├─ DashboardView
  │  └─ Matches/drafts loaded
  │
  ├─ TeamManagementWidget
  │  ├─ Current team selected
  │  └─ Current player selected
  │
  ├─ FormationPanel
  │  ├─ Selected team
  │  ├─ Assigned players to slots
  │  ├─ Selected libero
  │  └─ Game method selected
  │
  └─ RosterSetupWidget
     ├─ Current match
     ├─ Selected team
     └─ Selected players
```

---

## Error Handling

```
Database Connection Error
  └─ VolleyballScoutApp.__init__()
     ├─ Try: DatabaseManager()
     └─ Except: Show error widget, disable sections

Missing Data
  └─ Individual widgets
     ├─ Check if query returns data
     ├─ Show "No data available" message
     └─ Gracefully disable related controls

Validation Errors
  └─ FormationPanel
     ├─ Check 6 starters + 1 libero
     ├─ Show error dialog
     └─ Prevent form submission
```

---

## Navigation Flow

```
      ┌──────────────────┐
      │ Application Start│
      └────────┬─────────┘
               │
        ┌──────▼───────┐
        │  Dashboard   │ ◄──┐
        │   (Default)  │    │
        └──────┬───────┘    │
               │            │
        ┌──────▼────────────┴──────────────┐
        │   User Clicks Navigation Button  │
        └──────┬─────────────────────────┬─┘
               │                         │
      ┌────────▼──────────┐    ┌────────▼──────────┐
      │ Teams & Players   │    │ Roster Setup      │
      │ (Management)      │    │ (Match Prep)      │
      └────────┬──────────┘    └────────┬──────────┘
               │                        │
      ┌────────▼──────────┐    ┌────────▼──────────┐
      │ Formation Setup   │    │ Scout & Video     │
      │ (Start Lineup)    │    │ (Live Scouting)   │
      └────────┬──────────┘    └────────┬──────────┘
               │                        │
      ┌────────▼──────────┐    ┌────────▼──────────┐
      │ Statistics        │    │ Any Section       │
      │ (Analysis)        │    │ (Any Time)        │
      └──────────────────┘    └───────────────────┘
```

---

## Future Enhancements

```
Phase 2:
  ├─ Video player with real VLC integration
  ├─ Event sync with video timestamps
  ├─ Advanced scout keyboard
  └─ Player statistics dashboard

Phase 3:
  ├─ Multi-user support
  ├─ Cloud sync (PostgreSQL)
  ├─ Real-time collaboration
  └─ Export to DataVolley (.dvw)

Phase 4:
  ├─ Mobile companion app
  ├─ Live streaming integration
  ├─ AI-powered analysis
  └─ Advanced tactics editor
```

---

**End of Architecture Documentation**

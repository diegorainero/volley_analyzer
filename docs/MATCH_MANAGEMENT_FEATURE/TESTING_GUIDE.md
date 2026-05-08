# Match Salvati - Testing Guide

## Pre-requisite Setup

### 1. Database Preparation
Assicurati che il database sia inizializzato e contenga almeno 2-3 squadre:

```bash
# Avvia l'applicazione
cd volley_analizer
python3 run_desktop.py

# Nel Team Management, aggiungi almeno 3 squadre:
# - Team A
# - Team B
# - Team C
```

### 2. Verify Database Schema
Verifica che la tabella `matches` abbia questi campi:
- `id` (PRIMARY KEY)
- `home_team_id` (FOREIGN KEY)
- `away_team_id` (FOREIGN KEY)
- `date` (DATETIME)
- `status` (VARCHAR, default='draft')
- `competition` (VARCHAR)
- `venue` (VARCHAR)

## Test Case 1: Create and Display New Match

### Steps
1. Navigate to "Match Management" tab
2. Select "Team A" in "Squadra A (Home)"
3. Select "Team B" in "Squadra B (Away)"
4. Set date to today
5. Enter "Serie A1" in "Competizione"
6. Enter "Pala Test" in "Impianto"
7. Click "Avvio Scout (Imposta Roster)"

### Expected Results
- ✅ Match creato e salvato in database (status='draft')
- ✅ Widget lista "Match Salvati" aggiornato automaticamente
- ✅ Nuovo match appare nella lista con icona ⏳
- ✅ Background: giallo chiaro (#FFF3CD)
- ✅ Testo: marrone scuro (#856404)
- ✅ Testo format: "⏳ Team A vs Team B - DD/MM/YYYY HH:MM"

### Debugging
```python
# Se il match non appare nella lista, controllare:
# 1. Match è stato salvato al DB?
with db.session_scope() as session:
    matches = session.query(Match).all()
    for m in matches:
        print(f"Match: {m.id}, {m.home_team.name} vs {m.away_team.name}, status={m.status}")

# 2. _load_saved_matches() è stato chiamato?
# Aggiungere print statement:
def _load_saved_matches(self):
    print("DEBUG: Loading saved matches...")
    self.matches_list_widget.clear()
    with self.db.session_scope() as session:
        matches = session.query(Match).order_by(Match.date.desc()).all()
        print(f"DEBUG: Found {len(matches)} matches")
        for match in matches:
            print(f"DEBUG: Adding match {match.id} - {match.status}")
```

## Test Case 2: Resume Incomplete Scout

### Setup
1. Create match "Team A vs Team B" (as in Test Case 1)
2. You're now in Roster Setup screen

### Steps
1. Quickly exit back to Match Management (close panel or use menu)
2. In "Match Salvati" list, click on "⏳ Team A vs Team B - DD/MM/YYYY"

### Expected Results
- ✅ Dialog appears: "Continua Scout"
- ✅ Message: "Vuoi continuare lo scouting di Team A vs Team B?"
- ✅ Two buttons: "Yes" and "No"

### Sub-test: Click Yes
1. Click "Yes" button

### Expected Results
- ✅ Dialog closes
- ✅ Signal `resume_match` is emitted with match_id
- ✅ `show_formation_panel()` is called
- ✅ Formation panel loads with existing match data
- ✅ User can resume scouting where they left off

### Sub-test: Click No
1. Click "No" button

### Expected Results
- ✅ Dialog closes
- ✅ No signal emitted
- ✅ User remains in Match Management
- ✅ Match still visible in list with ⏳ status

## Test Case 3: Complete Match and Verify Status Change

### Setup
1. Have a match in "draft" state in the list

### Steps (Manual Database Update)
1. Open database browser (DB Browser for SQLite)
2. Find the match record
3. Update `status` from 'draft' to 'completed'
4. Save changes

### Alternative Steps (Via Code)
```python
# In a Python script or DB console:
from volleyball_scout.core.database import DatabaseManager
db = DatabaseManager()

with db.session_scope() as session:
    match = session.query(Match).filter(Match.id == 1).first()
    if match:
        match.status = 'completed'
        session.commit()
        print(f"Match {match.id} status updated to 'completed'")
```

### Steps (UI)
1. Navigate back to Match Management
2. List should refresh with new color

### Expected Results
- ✅ Match color changes to green (#D4EDDA)
- ✅ Match text color changes to dark green (#155724)
- ✅ Icon changes to ✅
- ✅ Text format: "✅ Team A vs Team B - DD/MM/YYYY HH:MM"

## Test Case 4: Click on Completed Match

### Setup
1. Have a completed match visible in the list with ✅

### Steps
1. Click on the completed match item

### Expected Results
- ✅ Dialog appears: "Match Completato"
- ✅ Message shows match details:
  - "Match Team A vs Team B"
  - "Stato: Completato"
  - "Data: DD/MM/YYYY HH:MM"
- ✅ Single "OK" button
- ✅ No action buttons (read-only)

### Sub-test: Click OK
1. Click "OK" button

### Expected Results
- ✅ Dialog closes
- ✅ User remains in Match Management
- ✅ List is unchanged

## Test Case 5: Multiple Matches Display

### Setup
1. Create 3 different matches:
   - Match 1: Team A vs Team B (set status='draft')
   - Match 2: Team B vs Team C (set status='completed')
   - Match 3: Team C vs Team A (set status='in_progress')

### Steps
1. Navigate to Match Management
2. Observe the list

### Expected Results
- ✅ All 3 matches visible in list
- ✅ Matches ordered by date (most recent first)
- ✅ Match 1: ⏳ yellow background
- ✅ Match 2: ✅ green background
- ✅ Match 3: ⏳ yellow background (in_progress treated as draft)
- ✅ Each item properly formatted with team names and date

### Visual Verification
```
┌─────────────────────────────────────────────────┐
│ ⏳ Team C vs Team A - 30/01/2025 14:15       │ ← in_progress
│ ✅ Team B vs Team C - 28/01/2025 18:00       │ ← completed
│ ⏳ Team A vs Team B - 28/01/2025 10:30       │ ← draft
└─────────────────────────────────────────────────┘
```

## Test Case 6: Styling and Layout

### Steps
1. Open Match Management
2. Observe "Crea Nuovo Match" group box
3. Observe "Match Salvati" group box
4. Hover over list items
5. Try to resize window

### Expected Results - Group Boxes
- ✅ Two separate QGroupBox widgets
- ✅ Titles are bold and clear
- ✅ Forms are contained within boxes
- ✅ Good visual separation

### Expected Results - List Widget
- ✅ Border is visible (1px solid #ddd)
- ✅ Border radius is subtle (5px)
- ✅ Items have padding (10px)
- ✅ Items have margin (2px top/bottom)
- ✅ Hover effect works (PyQt default)
- ✅ Selection highlight works (PyQt default)

### Expected Results - Responsive
- ✅ Widgets scale with window resize
- ✅ List items remain readable
- ✅ No text overflow
- ✅ No layout breaking

## Test Case 7: Edge Cases

### Empty List
1. Delete all matches from database
2. Navigate to Match Management
3. Observe list

### Expected Results
- ✅ List is empty (no items)
- ✅ Group box "Match Salvati" still visible
- ✅ No errors in console

### Missing Team Name
1. Create match where home_team_id is NULL
2. Observe list

### Expected Results
- ✅ Match appears with "?" instead of team name
- ✅ Format: "⏳ ? vs Team B - DD/MM/YYYY HH:MM"
- ✅ No crash or exception

### NULL Date
1. Create match where date is NULL
2. Observe list

### Expected Results
- ✅ Match appears with "?" instead of date
- ✅ Format: "⏳ Team A vs Team B - ?"
- ✅ No crash or exception

### Very Long Team Names
1. Create teams with very long names (100+ chars)
2. Observe list

### Expected Results
- ✅ Text is truncated gracefully (PyQt default)
- ✅ List is still readable
- ✅ No layout breaking

## Test Case 8: Data Refresh

### Steps
1. Create Match 1 in UI
2. Without closing app, open database browser
3. Add Match 2 directly to database
4. Return to app and navigate away from Match Management
5. Navigate back to Match Management

### Expected Results
- ✅ Match 1 is visible (created via UI)
- ✅ Match 2 is visible (added to DB externally)
- ✅ List refreshed on view change
- ✅ Both matches displayed correctly

## Test Case 9: Signal Connection

### Steps (Code Inspection)
1. Open `volleyball_scout/ui/main_window.py`
2. Find line: `self.match_view.resume_match.connect(...)`
3. Verify it's connected to `self.show_formation_panel`

### Expected Code Location
```python
# In VolleyballScoutMainWindow.init_ui()
self.match_view.resume_match.connect(self.show_formation_panel)
```

### Verification
- ✅ Signal is defined in MatchManagementWidget class
- ✅ Signal is emitted in _on_match_clicked() for draft/in_progress
- ✅ Signal is connected in main window
- ✅ Formation panel handler exists and accepts match_id

## Performance Test

### Setup
1. Create 50+ matches in database

### Steps
1. Navigate to Match Management
2. Observe load time
3. Scroll through list
4. Click on items

### Expected Results
- ✅ List loads in <1 second
- ✅ Scrolling is smooth
- ✅ Clicks are responsive
- ✅ No UI freezing
- ✅ No memory leaks (observable)

### Optimization Notes
If performance is poor:
```python
# Consider pagination or lazy loading:
def _load_saved_matches(self, limit=20):
    matches = session.query(Match)\\
        .order_by(Match.date.desc())\\
        .limit(limit)\\
        .all()
```

## Browser Compatibility (N/A)
This is a desktop application using PyQt6, not web-based.

## Conclusion Checklist

- [ ] Test Case 1: Create and Display ✓
- [ ] Test Case 2: Resume Scout ✓
- [ ] Test Case 3: Complete Match ✓
- [ ] Test Case 4: Completed Dialog ✓
- [ ] Test Case 5: Multiple Matches ✓
- [ ] Test Case 6: Styling ✓
- [ ] Test Case 7: Edge Cases ✓
- [ ] Test Case 8: Data Refresh ✓
- [ ] Test Case 9: Signal Connection ✓
- [ ] Performance Test ✓

All tests passed? Feature is ready for release! 🎉

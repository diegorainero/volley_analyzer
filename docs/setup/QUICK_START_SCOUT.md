# 🏐 Volleyball Scout - Quick Start Guide

## 🚀 Launch in 30 Seconds

```bash
cd volley_analizer
python3 main.py
```

Then select: **2** (Volleyball Scout)

✨ **The app opens with a sidebar menu connecting all features!**

---

## 🎯 What You See

A window with:
- **LEFT:** Sidebar with 6 section buttons
- **RIGHT:** Content area (changes when you click buttons)

```
┌─────────────────────────────────────────┐
│ 🏐 VOLLEYBALL SCOUT                    │
├──────────────┬──────────────────────────┤
│ 📊 Dashboard │                          │
│ 👥 Teams     │  Content displays here   │
│ 📋 Roster    │  (changes per section)   │
│ 🏐 Formation │                          │
│ 📝 Scout     │                          │
│ 📈 Statistics│                          │
└──────────────┴──────────────────────────┘
```

---

## 📋 6 Main Sections

### 1. 📊 Dashboard (Default)
Shows all your matches and draft sessions.
- **Left side:** All matches (color-coded by status)
- **Right side:** Drafts in progress

### 2. 👥 Team & Players
Manage your teams and players.
- Add/edit/delete teams
- Add/edit/delete players
- Assign player roles

### 3. 📋 Roster Setup
Prepare a match with specific players.
- Select a match
- Choose which players participate
- Continue to formation

### 4. 🏐 Formation Setup
**The star feature!** Set up your starting lineup.
- Drag players to formation positions
- Assign 1 libero (special player)
- Confirm to save

### 5. 📝 Scout & Video
Live scouting during the match.
- Event buttons (Attack, Block, Serve, etc.)
- Video player (for match recording)
- Real-time tracking

### 6. 📈 Statistics
View match statistics and player performance.
- Match summary
- Player stats
- Export options

---

## ✅ Common Workflow

### Step 1: Create Teams & Players
1. Click **"👥 Team & Players"**
2. Click **"Aggiungi Squadra"** (Add Team)
3. Enter team name, click Save
4. Select team, add players with numbers and roles

### Step 2: Create a Match
*(In Dashboard - future feature)*

### Step 3: Set Up Roster
1. Click **"📋 Roster Setup"**
2. Select your match
3. Check the players who will participate
4. Click **"Avanti"** (Next)

### Step 4: Set Formation
1. Click **"🏐 Formation Setup"**
2. **Drag** player circles into the 6 slots
3. **Select** 1 libero
4. Click **"Conferma Formazione"** (Confirm)

### Step 5: Scout the Match
1. Click **"📝 Scout & Video"**
2. Click event buttons as they happen
3. Watch the video or live stream
4. Events auto-save

### Step 6: View Statistics
1. Click **"📈 Statistics"**
2. See match summary
3. Export if needed

---

## 🎨 Color Coding

| Color | Meaning |
|-------|---------|
| 🔲 Light Gray | Match is DRAFT (not started) |
| ⏳ Light Yellow | Match is IN PROGRESS |
| ✅ Light Green | Match is COMPLETED |
| 🔵 Dark Blue (Menu) | Not selected |
| 🔵 Bright Blue (Menu) | Currently selected |

---

## 💾 Your Data

Everything is automatically saved to:
- **SQLite Database:** `~/.volleyball_scout/data/scout.db`
- Or cloud (PostgreSQL) if you set up `DATABASE_URL`

No manual saving needed!

---

## ⌨️ Keyboard Tips

- **Tab** to move between fields
- **Enter** to confirm dialogs
- **Click any button** to switch sections
- **Drag and drop** for formation setup

---

## ❓ Troubleshooting

### "❌ Database Connection Error"
```bash
# Check if database exists
ls ~/.volleyball_scout/data/

# If empty, run migrations
python3 -m alembic upgrade head
```

### App won't start
```bash
# Make sure PyQt6 is installed
pip3 install PyQt6 SQLAlchemy
```

### Can't see match cards
- You might not have created any matches yet
- Go to **Team & Players** to add data first
- Database needs teams to create matches

---

## 🔧 Advanced

### Using PostgreSQL (Cloud)
Create `.env` in `volley_analizer/`:
```
DATABASE_URL=postgresql://user:pass@host:5432/volleyball_scout
```

### Applying Database Updates
```bash
cd volley_analizer
python3 -m alembic upgrade head
```

### Direct Launch Without Main Menu
```bash
cd volley_analizer
python3 -m volleyball_scout.ui.app
```

---

## 📚 More Documentation

- **Detailed Guide:** `volleyball_scout/ui/docs/INTEGRATED_UI_GUIDE.md`
- **Architecture:** `volleyball_scout/ui/docs/UI_ARCHITECTURE.md`
- **Integration Summary:** `INTEGRATION_SUMMARY.md`

---

## 🎯 Pro Tips

1. **Test with sample data first**
   - Create a test team
   - Add test players
   - Try the formation panel

2. **Formation setup keyboard**
   - Drag circles into slots
   - Can drag OUT to remove
   - Must have 6 + 1 libero

3. **Save frequently**
   - All changes auto-save
   - But you can force DB update in Statistics → button

4. **Use the sidebar**
   - Always visible
   - Fast navigation
   - Shows which section is active

5. **Database cleanup**
   - Delete unused teams/players
   - Archive old matches
   - Export completed matches

---

## 🚦 Status Indicators

**Match Status Colors:**
- **🔲 Bozza (Draft)** - Not started, being prepared
- **⏳ In Corso (In Progress)** - Live match happening
- **✅ Completato (Completed)** - Match finished, data complete

**Menu Button Status:**
- **Dark Blue** - Other sections (not active)
- **Bright Blue** - Current section (active)

---

## 🆘 Need Help?

1. **Check console output** - Look for error messages
2. **Read the logs** - Database operations logged
3. **Verify database** - Make sure data exists
4. **Restart app** - Simple refresh often helps
5. **Check documentation** - Extensive guides available

---

## ⭐ Features You'll Love

✨ **Drag & Drop Formation Setup**
- Click and drag players to court positions
- Visual feedback while dragging
- Automatic validation (6 + 1)

✨ **Real-time Updates**
- All changes saved instantly
- No "Save" button needed
- Always synced with database

✨ **Professional Interface**
- Clean, organized menu system
- Color-coded status
- Responsive design

✨ **Multi-Feature Support**
- Team management
- Roster planning
- Formation setup
- Live scouting
- Statistics tracking

---

## 🏐 Ready to Scout?

**You're all set!** 

Launch the app and start using Volleyball Scout. The interface is designed to be intuitive:
1. Navigate via sidebar
2. Follow the natural workflow
3. Let the app handle data management
4. Focus on scouting!

**Buona partita!** 🏐

---

*For detailed information, see the full documentation in the `volleyball_scout/ui/docs/` folder.*

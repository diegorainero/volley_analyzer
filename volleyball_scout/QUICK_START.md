# 🚀 Quick Start - Volleyball Scout

## Prerequisites

- Python 3.13+
- Virtual environment (`venv`) activated
- Dependencies installed: `pip install -r requirements.txt`

## ⚡ Quick Launch

### Option 1: System Health Check (Recommended First)
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer

# Check that everything is working
venv/bin/python -m volleyball_scout.check_system
```

You should see:
```
✅ Core Imports
✅ Database Connection
✅ UI Core Imports
✅ Formation Panel
✅ Scout Panel
✅ Exporters
🎉 ALL TESTS PASSED (6/6)
```

### Option 2: Launch the UI Application
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer

# Start the PyQt6 application
venv/bin/python -m volleyball_scout.ui
```

This will:
- Initialize the SQLite database at `~/.volleyball_scout/data/scout.db`
- Open the main window with the dashboard
- Show available matches and draft sessions
- Allow you to create new matches and scout them

### Option 3: Run CLI Demo
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer

# Run the CLI demonstration
venv/bin/python -m volleyball_scout.main
```

This demonstrates:
- Database connection
- Creating demo teams and players
- Session management

## 📋 What's Included

### Core Features
✅ **Database Management**
- SQLite local storage (development)
- PostgreSQL cloud support (production)
- SQLAlchemy ORM

✅ **Match Management**
- Create new matches
- Select teams and players
- Manage rosters

✅ **Formation Panel**
- Visual court representation (2D court with players)
- Rotation logic (1→6→5→4→3→2 position sequence)
- Libero management
- Game method detection (P-S-C vs P-C-S)
- Switch between teams side-by-side

✅ **Scout Interface**
- Real-time event logging
- Formation display and editing
- Draft session persistence
- Video player integration

✅ **Exporters**
- DataVolley format export

## 🗂️ Project Structure

```
volleyball_scout/
├── core/               # Business logic
│   ├── database.py    # DB manager
│   ├── models.py      # Data models
│   └── engines/       # Stats & sync
├── ui/                # PyQt6 Interface
│   ├── app.py         # Main window
│   ├── formation_panel.py
│   ├── scout_panel.py
│   └── drafts/        # Draft management
└── exporters/         # Export formats
```

## 🐛 Troubleshooting

### ModuleNotFoundError
**Problem**: `No module named 'volleyball_scout'`

**Solution**: Always use `-m` flag to run as module:
```bash
# ✅ CORRECT
venv/bin/python -m volleyball_scout.ui

# ❌ WRONG
venv/bin/python volleyball_scout/ui/main_window.py
```

### Database Connection Error
**Problem**: Can't connect to database

**Solution**: The database directory will be created automatically at:
```
~/.volleyball_scout/data/scout.db
```

If you want to use a cloud database, set the environment variable:
```bash
export DATABASE_URL=postgresql://user:pass@host/dbname
```

### Import Errors
**Problem**: Specific module imports fail

**Solution**: Run the health check to diagnose:
```bash
venv/bin/python -m volleyball_scout.check_system
```

## 🔗 Related Documentation

- [Structure & Architecture](./STRUCTURE.md)
- [UI Documentation](./ui/README.md)
- [Formation Panel Details](../FORMATION_QUICK_START.md)

## 📧 Support

If you encounter issues:
1. Run `check_system.py` to diagnose
2. Check the database file exists: `~/.volleyball_scout/data/scout.db`
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

---

**Ready to start?** Launch the app:
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
venv/bin/python -m volleyball_scout.ui
```

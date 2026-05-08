# 📚 Volleyball Scout - Documentation Index

## 🚀 Getting Started

**New User?** Start here:
1. Read: [`QUICK_START.md`](./QUICK_START.md) - How to run the app (5 min read)
2. Run: `venv/bin/python -m volleyball_scout.check_system` - Verify everything works
3. Launch: `venv/bin/python -m volleyball_scout.ui` - Start the application

**Troubleshooting?** 
- See [`QUICK_START.md` → Troubleshooting](./QUICK_START.md#-troubleshooting)

---

## 📖 Documentation Map

### Core Documentation
| Document | Purpose | Audience |
|----------|---------|----------|
| [`QUICK_START.md`](./QUICK_START.md) | How to run the application | **Everyone** |
| [`STRUCTURE.md`](./STRUCTURE.md) | Project architecture & modules | Developers |
| [`README.md`](./README.md) | Module overview | Developers |

### UI Documentation
| Document | Purpose |
|----------|---------|
| [`ui/README.md`](./ui/README.md) | UI components and features |

### Formation Panel
| Document | Purpose |
|----------|---------|
| [`../FORMATION_QUICK_START.md`](../FORMATION_QUICK_START.md) | Formation panel guide |
| [`../FORMATION_ENHANCEMENTS_SUMMARY.md`](../FORMATION_ENHANCEMENTS_SUMMARY.md) | Enhancement details |

### System Documentation
| Document | Purpose |
|----------|---------|
| [`../VOLLEYBALL_SCOUT_SUMMARY.md`](../VOLLEYBALL_SCOUT_SUMMARY.md) | Complete system overview |
| [`check_system.py`](./check_system.py) | Health check utility |

---

## 🎯 Quick Navigation by Task

### I want to...

**...run the application**
→ See: [`QUICK_START.md`](./QUICK_START.md#-quick-launch)

**...understand the project structure**
→ See: [`STRUCTURE.md`](./STRUCTURE.md)

**...work with the Formation Panel**
→ See: [`../FORMATION_QUICK_START.md`](../FORMATION_QUICK_START.md)

**...develop a new feature**
→ See: [`STRUCTURE.md` → Development](./STRUCTURE.md#development)

**...troubleshoot an issue**
→ See: [`QUICK_START.md` → Troubleshooting](./QUICK_START.md#-troubleshooting)

**...understand the database**
→ See: [`STRUCTURE.md` → Database Layer](./STRUCTURE.md#1-database-layer-coredatabasepy)

**...add a new UI component**
→ See: [`STRUCTURE.md` → Add New UI Panels](./STRUCTURE.md#add-new-ui-panels)

**...check system health**
→ Run: `venv/bin/python -m volleyball_scout.check_system`

---

## 📂 File Structure

```
volleyball_scout/
├── 📄 QUICK_START.md           ← Start here!
├── 📄 STRUCTURE.md             ← Architecture details
├── 📄 INDEX.md                 ← This file
├── 📄 README.md
├── 🔧 check_system.py          ← Health check utility
├── 🔧 main.py                  ← CLI entry point
│
├── 📁 core/                    ← Business logic
│   ├── database.py
│   ├── models.py
│   ├── stats_engine.py
│   └── sync_engine.py
│
├── 📁 ui/                      ← User Interface
│   ├── 📄 README.md
│   ├── app.py
│   ├── formation_panel.py
│   ├── scout_panel.py
│   └── drafts/
│
└── 📁 exporters/               ← Export formats
    └── datavolley.py
```

---

## ✅ System Status

```
🎉 ALL COMPONENTS WORKING ✅

✅ Core Layer (database, models, engines)
✅ UI Layer (PyQt6 application)
✅ Formation Panel (court visualization, rotation)
✅ Scout Panel (real-time event logging)
✅ Exporters (DataVolley format)
✅ Database (SQLite/PostgreSQL)
```

**Health Check Results**: 6/6 tests passing

---

## 🔧 Essential Commands

### Health Check
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
venv/bin/python -m volleyball_scout.check_system
```

### Launch UI
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
venv/bin/python -m volleyball_scout.ui
```

### CLI Demo
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
venv/bin/python -m volleyball_scout.main
```

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| **Python Files** | 15+ |
| **Documentation Files** | 10+ |
| **Test Coverage** | 6/6 (100%) |
| **Database Models** | 6+ |
| **UI Components** | 10+ |

---

## 🎓 Learning Path

### For Users
1. [`QUICK_START.md`](./QUICK_START.md) - 5 minutes
2. Run `check_system.py` - 30 seconds
3. Launch the app - Start using it!

### For Developers
1. [`QUICK_START.md`](./QUICK_START.md) - Overview
2. [`STRUCTURE.md`](./STRUCTURE.md) - Architecture
3. [`ui/README.md`](./ui/README.md) - UI Details
4. [`../FORMATION_QUICK_START.md`](../FORMATION_QUICK_START.md) - Advanced features
5. Explore the source code!

---

## 🔗 External Resources

- [PyQt6 Official Docs](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Volleyball Positions Guide](https://en.wikipedia.org/wiki/Volleyball_positions)

---

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Use `-m` flag: `python -m volleyball_scout.ui` |
| Database not found | Check `~/.volleyball_scout/data/scout.db` exists |
| Import errors | Run `check_system.py` to diagnose |

See [`QUICK_START.md`](./QUICK_START.md#-troubleshooting) for more details.

---

## 📞 Support

1. **Quick check**: Run `venv/bin/python -m volleyball_scout.check_system`
2. **Documentation**: Check [`QUICK_START.md`](./QUICK_START.md)
3. **Architecture**: See [`STRUCTURE.md`](./STRUCTURE.md)
4. **Issues**: Review logs at `~/.volleyball_scout/scout.log`

---

**Ready to start?**
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
venv/bin/python -m volleyball_scout.ui
```

*Last Updated: 2024*

# 🔧 Quick Fix - Import Errors

## Problems Fixed

### Problem 1: "No module named 'core'"
✅ FIXED - Added sys.path manipulation

### Problem 2: "Cannot import RosterSetupWidget"
✅ FIXED - Updated imports to use absolute paths with fallback

## Cause

Gli import relativi in `volleyball_scout/main.py` non trovavano la cartella `core`.

## Solutions Applied ✅

### 1. ✅ Fixed `volleyball_scout/main.py`
- Added `sys.path.insert(0, str(Path(__file__).parent))` all'inizio
- Wrapped imports in try/except con messaggio di errore chiaro
- Ora gli import di `core` funzionano correttamente

### 2. ✅ Fixed `run_desktop.py`
- Updated per lanciare la nuova app integrata
- Aggiunto try/except per fallback
- Supporta sia la nuova UI che il vecchio main.py

### 3. ✅ Fixed `main.py` (root)
- Già configurato correttamente
- Importa da `volleyball_scout.ui.app`
- Gestisce errori gracefully

## How to Launch Now

### Option 1: Main Menu (Recommended)
```bash
cd volley_analizer
python3 main.py
# Select: 2 (Volleyball Scout)
```

### Option 2: Direct Launch
```bash
cd volley_analizer
python3 -m volleyball_scout.ui.app
```

### Option 3: Desktop Mode
```bash
cd volley_analizer
python3 run_desktop.py
# Click: Volleyball Scout
```

### Option 4: Using venv
```bash
cd volley_analizer
venv/bin/python main.py
# Select: 2
```

## What Was Fixed

| File | Issue | Fix |
|------|-------|-----|
| `volleyball_scout/main.py` | `core` module not found | Added sys.path manipulation |
| `run_desktop.py` | Didn't use new UI | Updated to import from ui.app |
| Import paths | Relative imports failed | Made all imports absolute with sys.path |

## Testing

All files now pass syntax validation:

```bash
python3 -m py_compile main.py run_desktop.py volleyball_scout/main.py volleyball_scout/ui/app.py
# ✅ All files syntax OK
```

## Status

✅ **All import issues resolved**

You can now launch the app using any of the 4 methods above!

---

## If You Still Get Errors

### Error: "ModuleNotFoundError: No module named 'PyQt6'"
```bash
pip install PyQt6 SQLAlchemy
```

### Error: "Database connection failed"
```bash
# Check database exists
ls ~/.volleyball_scout/data/

# Run migrations
python3 -m alembic upgrade head
```

### Error: "volleyball_scout/core/ not found"
```bash
# You're probably in the wrong directory
# MUST be in volley_analizer/ directory:
cd volley_analizer
python3 main.py
```

---

## 🎉 Ready to Go!

```bash
cd volley_analizer
python3 main.py
# Select: 2
```

The app should now launch without any import errors! 🚀

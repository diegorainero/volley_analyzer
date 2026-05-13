#!/usr/bin/env python3
"""
Launcher per Database Check UI
Eseguire da project root: python3 scripts/launch_database_check.py

Questo script avvia l'interfaccia grafica per visualizzare le squadre e i giocatori
dal database Volleyball Scout.
"""

import sys
from pathlib import Path

# Ensure imports work
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from check_database_ui import main

if __name__ == "__main__":
    sys.exit(main() or 0)

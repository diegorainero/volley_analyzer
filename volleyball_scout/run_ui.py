#!/usr/bin/env python3
"""
Launcher per Volleyball Scout UI
Eseguire da project root: python3 volleyball_scout/run_ui.py
oppure: python3 -m volleyball_scout.run_ui
"""

import sys
from pathlib import Path

# Ensure volleyball_scout is importable
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from volleyball_scout.ui.app import main

if __name__ == "__main__":
    main()

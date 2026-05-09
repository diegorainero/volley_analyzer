"""
Volleyball Scout - Main Entry Point
Compatible with both direct and module execution
"""

import sys

# Questo serve come wrapper entry point
# Quando viene eseguito come: python -m volleyball_scout.ui.main_window
# Importa e esegue main() da app.py

if __name__ == "__main__":
    from volleyball_scout.ui.app_dark import main

    sys.exit(main() or 0)

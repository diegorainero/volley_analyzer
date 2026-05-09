"""
Volleyball Scout - UI Entry Point
Lanciare con: python -m volleyball_scout.ui
"""

import sys

from volleyball_scout.ui.app_dark import main

if __name__ == "__main__":
    sys.exit(main() or 0)

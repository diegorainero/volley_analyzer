#!/usr/bin/env python3
"""
Test dello toggle Light/Dark theme
"""

import sys
from pathlib import Path

# Test che il file ha sintassi valida
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from volleyball_scout.ui.app_dark import DARK_STYLESHEET, LIGHT_STYLESHEET

    print("✅ Stylesheet importati con successo")

    # Verifica che entrambi gli stylesheet siano non-vuoti
    assert len(DARK_STYLESHEET) > 100, "DARK_STYLESHEET troppo corto"
    assert len(LIGHT_STYLESHEET) > 100, "LIGHT_STYLESHEET troppo corto"

    # Verifica che abbiano colori diversi
    assert "#1e1e1e" in DARK_STYLESHEET, "Dark background not found in DARK_STYLESHEET"
    assert "#ffffff" in LIGHT_STYLESHEET, (
        "Light background not found in LIGHT_STYLESHEET"
    )

    print("✅ DARK_STYLESHEET OK:")
    print(f"  - Lunghezza: {len(DARK_STYLESHEET)} caratteri")
    print(f"  - Contiene dark background: #1e1e1e")

    print("✅ LIGHT_STYLESHEET OK:")
    print(f"  - Lunghezza: {len(LIGHT_STYLESHEET)} caratteri")
    print(f"  - Contiene light background: #ffffff")

    print("\n✅ Test dei stylesheet completato con successo!")

except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

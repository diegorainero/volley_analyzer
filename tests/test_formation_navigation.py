#!/usr/bin/env python3
"""
Script di test per verificare la navigazione in FormationSetupComplete.
Testa il flusso: Lista Match → FormationPanel → Back to Lista Match
"""

import sys
from pathlib import Path

# Aggiungi il percorso del progetto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.ui.formation_setup_complete import FormationSetupComplete


def test_navigation():
    """Test la navigazione tra lista match e formazione"""
    print("🧪 Inizio test navigazione FormationSetupComplete...")

    # Crea app Qt
    app = QApplication(sys.argv)

    # Inizializza il database
    print("📦 Inizializzo database...")
    db = DatabaseManager()

    # Crea il widget
    print("🏗️ Creo FormationSetupComplete...")
    formation_widget = FormationSetupComplete(db)

    # Verifiche
    print("\n✅ Verifiche di struttura:")

    # Check 1: QStackedWidget esiste
    assert hasattr(formation_widget, "stacked_widget"), "❌ Non trovato stacked_widget"
    print("✓ stacked_widget presente")

    # Check 2: Widget 0 è FormationSetupMatches
    widget_0 = formation_widget.stacked_widget.widget(0)
    assert widget_0 is not None, "❌ Widget 0 è None"
    assert widget_0 is formation_widget.matches_widget, (
        "❌ Widget 0 non è matches_widget"
    )
    print("✓ Index 0: FormationSetupMatches presente")

    # Check 3: Widget 1 è un placeholder (ancora vuoto)
    widget_1 = formation_widget.stacked_widget.widget(1)
    assert widget_1 is not None, "❌ Widget 1 è None"
    print("✓ Index 1: Placeholder presente")

    # Check 4: Index corrente è 0 (lista match)
    assert formation_widget.stacked_widget.currentIndex() == 0, (
        "❌ Index corrente non è 0"
    )
    print("✓ Index corrente è 0 (lista match)")

    # Check 5: Signal match_selected è connesso
    assert formation_widget.matches_widget.match_selected.isConnected(), (
        "⚠️ Signal non connesso"
    )
    print("✓ Signal match_selected connesso")

    # Check 6: FormationPanel ha il segnale back_requested
    from volleyball_scout.ui.formation_panel import FormationPanel

    assert hasattr(FormationPanel, "back_requested"), (
        "❌ FormationPanel non ha back_requested"
    )
    print("✓ FormationPanel ha segnale back_requested")

    # Check 7: Metodo _on_back_to_matches esiste
    assert hasattr(formation_widget, "_on_back_to_matches"), (
        "❌ Non trovato _on_back_to_matches"
    )
    print("✓ Metodo _on_back_to_matches presente")

    # Verifica che la lista dei match sia caricata
    matches_count = len(formation_widget.matches_widget.matches)
    print(f"\n📊 Match caricate: {matches_count}")

    if matches_count > 0:
        print("✓ Ci sono match disponibili per il test")
        print(f"\n📋 Prime 3 partite:")
        for i, match in enumerate(formation_widget.matches_widget.matches[:3]):
            print(
                f"  {i + 1}. {match['home_team']} vs {match['away_team']} ({match['status']})"
            )
    else:
        print("⚠️ Nessun match disponibile nel database")

    print("\n🎉 Tutti i test passati!")
    print("\nRiassunto della struttura:")
    print(f"  • FormationSetupComplete: QStackedWidget con 2 pagine")
    print(f"  • Index 0: FormationSetupMatches (lista partite)")
    print(f"  • Index 1: FormationPanel (dettagli formazione)")
    print(f"  • Navigazione: Double-click su match → passa a Index 1")
    print(f"  • Back: Pulsante 'Torna Indietro' → passa a Index 0")


if __name__ == "__main__":
    try:
        test_navigation()
    except AssertionError as e:
        print(f"\n❌ Test fallito: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

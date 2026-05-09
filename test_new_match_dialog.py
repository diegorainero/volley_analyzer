#!/usr/bin/env python3
"""
Test per NewMatchDialog e FormationSetupMatches
Verifica che il pulsante "Nuova Partita" funzioni correttamente
"""

import sys
from datetime import datetime

# Aggiungi il percorso al progetto
sys.path.insert(0, ".")

from PyQt6.QtWidgets import QApplication

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Match, Team


def setup_test_data(db_manager):
    """Crea dati di test nel database"""
    try:
        with db_manager.session_scope() as session:
            # Verifica se ci sono squadre
            existing_teams = session.query(Team).count()
            if existing_teams == 0:
                print("📝 Creando squadre di test...")
                team1 = Team(name="Team A", short_name="A", category="Test")
                team2 = Team(name="Team B", short_name="B", category="Test")
                session.add(team1)
                session.add(team2)
                session.flush()
                print("✅ Squadre create")
            else:
                print(f"✅ Database contiene {existing_teams} squadre")

    except Exception as e:
        print(f"⚠️ Error setting up test data: {e}")
        import traceback

        traceback.print_exc()


def test_new_match_dialog():
    """Test il NewMatchDialog"""
    try:
        print("\n" + "=" * 60)
        print("🧪 TEST: NewMatchDialog")
        print("=" * 60)

        # Inizializza l'app Qt
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Crea il database manager
        print("📦 Inizializzo il database...")
        db_manager = DatabaseManager()

        # Setup test data
        setup_test_data(db_manager)

        # Importa NewMatchDialog
        from volleyball_scout.ui.new_match_dialog import NewMatchDialog

        print("✅ NewMatchDialog importato correttamente")

        # Crea il dialog
        print("🔧 Creando NewMatchDialog...")
        dialog = NewMatchDialog(db_manager)
        print("✅ Dialog creato")

        # Verifica che i team siano stati caricati
        print(f"📋 Team caricati: {len(dialog.teams)}")
        for team in dialog.teams:
            print(f"  - {team['name']} (ID: {team['id']})")

        # Verifica che i widget siano disponibili
        assert hasattr(dialog, "combo_home"), "combo_home non trovato"
        assert hasattr(dialog, "combo_away"), "combo_away non trovato"
        assert hasattr(dialog, "date_time_edit"), "date_time_edit non trovato"
        assert hasattr(dialog, "line_venue"), "line_venue non trovato"
        assert hasattr(dialog, "text_notes"), "text_notes non trovato"
        print("✅ Tutti i widget sono disponibili")

        # Testa la validazione
        print("\n🔍 Test validazione:")
        is_valid, msg = dialog._validate_input()
        print(f"  - Validazione (team non selezionati): {not is_valid}")
        assert not is_valid, "La validazione dovrebbe fallire senza team"
        print(f"  - Messaggio: {msg}")

        # Seleziona i team
        if len(dialog.teams) >= 2:
            dialog.combo_home.setCurrentIndex(1)  # Primo team reale
            dialog.combo_away.setCurrentIndex(2)  # Secondo team reale
            is_valid, msg = dialog._validate_input()
            print(f"  - Validazione (team selezionati): {is_valid}")
            assert is_valid, f"La validazione dovrebbe passare: {msg}"
            print("✅ Validazione passata")
        else:
            print("⚠️ Non ci sono abbastanza team per testare")

        print("\n" + "=" * 60)
        print("✅ TEST PASSED: NewMatchDialog")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_formation_setup_matches():
    """Test il FormationSetupMatches con il pulsante Nuova Partita"""
    try:
        print("\n" + "=" * 60)
        print("🧪 TEST: FormationSetupMatches")
        print("=" * 60)

        # Inizializza l'app Qt
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Crea il database manager
        print("📦 Inizializzo il database...")
        db_manager = DatabaseManager()

        # Setup test data
        setup_test_data(db_manager)

        # Importa FormationSetupMatches
        from volleyball_scout.ui.formation_setup_complete import FormationSetupMatches

        print("✅ FormationSetupMatches importato correttamente")

        # Crea il widget
        print("🔧 Creando FormationSetupMatches...")
        widget = FormationSetupMatches(db_manager)
        print("✅ Widget creato")

        # Verifica che i widget siano disponibili
        assert hasattr(widget, "matches_table"), "matches_table non trovato"
        assert hasattr(widget, "_load_matches"), "_load_matches non trovato"
        assert hasattr(widget, "_on_new_match_clicked"), (
            "_on_new_match_clicked non trovato"
        )
        print("✅ Tutti i metodi e widget sono disponibili")

        # Verifica che i match siano stati caricati
        print(f"📋 Match caricati: {len(widget.matches)}")
        for match in widget.matches:
            print(
                f"  - {match['home_team']} vs {match['away_team']} ({match['status']})"
            )

        print("\n" + "=" * 60)
        print("✅ TEST PASSED: FormationSetupMatches")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🏐 VOLLEYBALL SCOUT - TEST NEW MATCH DIALOG")
    print("=" * 60)

    # Run tests
    test1_passed = test_new_match_dialog()
    test2_passed = test_formation_setup_matches()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"NewMatchDialog:       {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"FormationSetupMatches: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 60)

    if test1_passed and test2_passed:
        print("\n✅ TUTTI I TEST PASSATI!")
        sys.exit(0)
    else:
        print("\n❌ ALCUNI TEST FALLITI")
        sys.exit(1)

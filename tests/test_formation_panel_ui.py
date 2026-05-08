"""
Test visivo per il FormationPanel con drag-drop
Eseguire con: python tests/test_formation_panel_ui.py
"""

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from volleyball_scout.ui.formation_panel import FormationPanel


def main():
    app = QApplication(sys.argv)

    # Dati di test
    teams = [{"id": 1, "name": "Attacco"}, {"id": 2, "name": "Cihsosla Volley"}]

    players_by_team = {
        1: [
            {"id": 1, "number": 1, "last_name": "Rossi", "role": "Palleggiatore"},
            {"id": 2, "number": 2, "last_name": "Bianchi", "role": "Schiacciatore"},
            {"id": 3, "number": 3, "last_name": "Verdi", "role": "Centrale"},
            {"id": 4, "number": 4, "last_name": "Gialli", "role": "Laterale"},
            {"id": 5, "number": 5, "last_name": "Neri", "role": "Schiacciatore"},
            {"id": 6, "number": 6, "last_name": "Rosa", "role": "Libero"},
            {"id": 7, "number": 7, "last_name": "Arancione", "role": "Centrale"},
            {"id": 8, "number": 8, "last_name": "Blu", "role": "Palleggiatore"},
        ],
        2: [
            {"id": 9, "number": 10, "last_name": "Marrone", "role": "Schiacciatore"},
            {"id": 10, "number": 11, "last_name": "Grigio", "role": "Centrale"},
            {"id": 11, "number": 12, "last_name": "Viola", "role": "Palleggiatore"},
            {"id": 12, "number": 13, "last_name": "Celeste", "role": "Laterale"},
            {"id": 13, "number": 14, "last_name": "Turchese", "role": "Schiacciatore"},
            {"id": 14, "number": 15, "last_name": "Magenta", "role": "Libero"},
            {"id": 15, "number": 16, "last_name": "Lime", "role": "Centrale"},
            {"id": 16, "number": 17, "last_name": "Navy", "role": "Libero"},
        ],
    }

    # Crea la finestra principale
    window = QMainWindow()
    window.setWindowTitle("Test FormationPanel - Drag & Drop")
    window.setGeometry(100, 100, 1600, 900)

    # Crea il pannello di formazione
    formation_panel = FormationPanel(teams, players_by_team)

    # Connetti il segnale di conferma
    def on_formation_confirmed(data):
        print("\n✅ Formazione Confermata!")
        print(f"Titolari: {data['titolari']}")
        print(f"Liberi: {data['libero']}")

    formation_panel.formation_confirmed.connect(on_formation_confirmed)

    # Imposta il pannello come widget principale
    window.setCentralWidget(formation_panel)

    # Mostra la finestra
    window.show()

    print("=" * 80)
    print("🏐 TEST FORMATION PANEL - DRAG & DROP")
    print("=" * 80)
    print("\n📋 Istruzioni:")
    print("1. Trascina i numeri dei giocatori (bottoni blu) negli slot gialli a destra")
    print("2. Trascina almeno 1 giocatore negli slot 'Liberi' a sinistra")
    print("3. Devi avere 6 titolari + 1 libero per squadra")
    print("4. Clicca sui numeri negli slot per rimuoverli")
    print("5. Premi 'Conferma Formazione' quando hai completato")
    print("\n💡 Suggerimenti:")
    print("   - Ogni slot evidenziato giallo è una drop zone")
    print("   - I bottoni diventano gialli quando selezionati")
    print("   - Puoi drag-drop da qualsiasi bottone ai vari slot")
    print("=" * 80 + "\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

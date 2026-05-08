import sys
from pathlib import Path


def main_menu():
    """Display the main menu for selecting application mode"""
    print("\n" + "=" * 80)
    print("🏐 VOLLEY ANALYZER - Main Menu")
    print("=" * 80)
    print("\nScegli modalità:")
    print("  1. 📹 Video Analisi")
    print("  2. 🏐 Volleyball Scout (Formation & Scouting)")
    print("  0. Esci")
    print("\n" + "-" * 80)
    scelta = input("Seleziona [0/1/2]: ").strip()
    return scelta


if __name__ == "__main__":
    scelta = main_menu()
    if scelta == "1":
        print("\n📹 Avviando Video Analisi...\n")
        from src.volley_analizer.ui.cli import main as video_main

        sys.exit(video_main())
    elif scelta == "2":
        print("\n🏐 Avviando Volleyball Scout...\n")
        from volleyball_scout.ui.app import main as scout_main

        sys.exit(scout_main() or 0)
    elif scelta == "0":
        print("\n👋 Arrivederci!\n")
        sys.exit(0)
    else:
        print("\n❌ Scelta non valida.\n")
        sys.exit(1)

from __future__ import annotations

import os
import sys

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"


def _should_reexec() -> bool:
    return (
        VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve()
    )


def _reexec_in_venv() -> None:
    env = os.environ.copy()
    env["VOLLEY_ANALYZER_REEXEC"] = "1"
    completed = subprocess.run(
        [str(VENV_PYTHON), str(Path(__file__).resolve())], env=env, check=False
    )
    raise SystemExit(completed.returncode)


if _should_reexec() and os.environ.get("VOLLEY_ANALYZER_REEXEC") != "1":
    _reexec_in_venv()

try:
    import cv2  # noqa: F401
except Exception as exc:
    python_cmd = Path(sys.executable)
    message = (
        "OpenCV non installato per questo interprete:\n"
        f"- python: {python_cmd}\n\n"
        "Installa le dipendenze in questo ambiente e riavvia:\n"
        f"  {python_cmd} -m pip install opencv-python PyQt6 numpy pandas\n"
    )
    raise SystemExit(message) from exc

from PyQt6.QtWidgets import QApplication, QMessageBox


def choose_mode():
    app = QApplication(sys.argv)
    msg = QMessageBox()
    msg.setWindowTitle("Scegli modalità")
    msg.setText("Vuoi avviare Video Analisi o Volleyball Scout?")
    video_btn = msg.addButton("Video Analisi", QMessageBox.ButtonRole.AcceptRole)
    scout_btn = msg.addButton("Volleyball Scout", QMessageBox.ButtonRole.AcceptRole)
    msg.exec()
    if msg.clickedButton() == video_btn:
        return "video"
    elif msg.clickedButton() == scout_btn:
        return "scout"
    return None


if __name__ == "__main__":
    scelta = choose_mode()
    if scelta == "video":
        from src.volley_analizer.ui.app import run

        raise SystemExit(run())
    elif scelta == "scout":
        # Launch integrated Volleyball Scout UI
        try:
            from volleyball_scout.ui.app_dark import main as scout_main

            raise SystemExit(scout_main() or 0)
        except ImportError as e:
            print(f"❌ Errore import Scout UI: {e}")
            print("   Fallback a main.py...")
            raise SystemExit(
                subprocess.call([sys.executable, "-m", "volleyball_scout.main"])
            )

#!/usr/bin/env python3
"""
Build script for Volleyball Scout
Crea eseguibili compilati per Linux, Windows e Mac con PyInstaller.

Usage:
    python scripts/build.py                          # build per piattaforma corrente
    python scripts/build.py --target windows          # specifica piattaforma
    python scripts/build.py --mode scout              # solo scout (default, ~80MB)
    python scripts/build.py --mode full               # scout + YOLO per video analisi (~300MB)
    python scripts/build.py --onefile                 # singolo eseguibile (vs --onedir)
    python scripts/build.py --clean                   # pulisci build precedenti
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "VolleyballScout"
VERSION = "1.0.0"
ENTRY_POINT = PROJECT_ROOT / "volleyball_scout" / "run_ui.py"


def detect_platform() -> str:
    raw = platform.system().lower()
    return {"linux": "linux", "windows": "windows", "darwin": "macos"}.get(raw, raw)


def make_entry_point() -> Path:
    """Crea entry point adattato per eseguibile compilato"""
    content = '''"""
Volleyball Scout - PyInstaller Entry Point
"""
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from volleyball_scout.ui.app_dark import main

if __name__ == "__main__":
    sys.exit(main() or 0)
'''
    ep = PROJECT_ROOT / ".build_entry.py"
    ep.write_text(content)
    return ep


def build_app(target: str, mode: str, onefile: bool, clean: bool):
    print(f"\n{'='*60}")
    print(f"🔨 Building {APP_NAME} v{VERSION}")
    print(f"🎯 Target: {target}")
    print(f"📦 Mode: {mode}")
    print(f"{'='*60}\n")

    entry = make_entry_point()

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean" if clean else None,
    ]
    cmd = [c for c in cmd if c]

    sep = ";" if target == "windows" else ":"

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if target in ("windows", "macos"):
        cmd.append("--windowed")

    if target == "macos":
        cmd.append("--osx-bundle-identifier")
        cmd.append("com.volleyballscout.app")

    cmd.extend(["--name", APP_NAME])
    cmd.extend(["--specpath", str(PROJECT_ROOT / "build")])

    # --- Data files ---
    # UI Assets (SVG icons, logo)
    assets = PROJECT_ROOT / "volleyball_scout" / "ui" / "assets"
    if assets.exists():
        cmd.extend(["--add-data", f"{assets}{sep}volleyball_scout/ui/assets"])

    # Alembic migrations
    alembic_ini = PROJECT_ROOT / "alembic.ini"
    if alembic_ini.exists():
        cmd.extend(["--add-data", f"{alembic_ini}{sep}."])
    alembic_dir = PROJECT_ROOT / "alembic"
    if alembic_dir.exists():
        cmd.extend(["--add-data", f"{alembic_dir}{sep}alembic"])

    # YOLO models (solo full mode)
    if mode == "full":
        models_dir = PROJECT_ROOT / "models"
        if models_dir.exists():
            cmd.extend(["--add-data", f"{models_dir}{sep}models"])

    # --- Hidden imports ---
    hidden = [
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtSvg",
        "PyQt6.QtPrintSupport",
        "sqlalchemy",
        "sqlalchemy.dialects.sqlite",
        "alembic",
        "alembic.config",
        "alembic.migration",
        "openpyxl",
        "reportlab",
        "volleyball_scout",
        "volleyball_scout.ui",
        "volleyball_scout.ui.assets",
        "volleyball_scout.ui.drafts",
        "volleyball_scout.core",
        "volleyball_scout.exporters",
    ]

    if mode == "full":
        hidden.extend([
            "torch",
            "ultralytics",
            "ultralytics.nn",
            "ultralytics.models",
            "ultralytics.engine",
            "cv2",
            "numpy",
            "pandas",
            "deep_sort_realtime",
        ])

    for h in hidden:
        cmd.extend(["--hidden-import", h])

    # --- Exclusions ---
    exclude = [
        "matplotlib",
        "PIL",
        "tkinter",
        "scipy",
        "notebook",
        "jupyter",
    ]
    if mode == "scout":
        exclude.extend(["torch", "ultralytics", "cv2", "deep_sort_realtime"])

    for e in exclude:
        cmd.extend(["--exclude-module", e])

    # --- Add entry point ---
    cmd.append(str(entry))

    # Clean previous builds
    for d in ["build", "dist"]:
        p = PROJECT_ROOT / d
        if p.exists() and clean:
            shutil.rmtree(p, ignore_errors=True)

    # Run PyInstaller
    print(f"🚀 Running PyInstaller...\n")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        print("\n❌ Build fallita!")
        entry.unlink(missing_ok=True)
        sys.exit(1)

    # --- Create distributable archive ---
    dist_dir = PROJECT_ROOT / "dist"
    app_dir = dist_dir / APP_NAME
    mode_tag = "full" if mode == "full" else ""
    suffix = f"-{mode_tag}" if mode_tag else ""
    base_name = f"{APP_NAME}-{VERSION}-{target}{suffix}"

    if not app_dir.exists():
        print(f"\n⚠️  App dir non trovata in {app_dir}, skippo archivio")
    else:
        if target == "windows":
            archive = dist_dir / f"{base_name}.zip"
            shutil.make_archive(str(dist_dir / base_name), "zip", str(app_dir))
        else:
            archive = dist_dir / f"{base_name}.tar.gz"
            shutil.make_archive(str(dist_dir / base_name), "gztar", str(app_dir))
        print(f"\n📦 Archivio: {archive}")

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"✅ Build completata!")
    print(f"📂 Eseguibile: {app_dir}")
    print(f"{'='*60}")

    # Cleanup
    entry.unlink(missing_ok=True)
    spec_path = PROJECT_ROOT / "build" / f"{APP_NAME}.spec"
    spec_path.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build Volleyball Scout per Linux, Windows e Mac"
    )
    parser.add_argument(
        "--target",
        choices=["linux", "windows", "macos", "auto"],
        default="auto",
        help="Piattaforma target (default: auto-detect)",
    )
    parser.add_argument(
        "--mode",
        choices=["scout", "full"],
        default="scout",
        help="scout=solo UI (~80MB), full=con YOLO/video (~300MB)",
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Singolo eseguibile (default: --onedir, piu' veloce)",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Pulisci build precedenti"
    )
    args = parser.parse_args()

    target = detect_platform() if args.target == "auto" else args.target

    # Verify PyInstaller is available
    try:
        import PyInstaller
    except ImportError:
        print("📦 PyInstaller non trovato. Installo...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"]
        )

    build_app(target, args.mode, args.onefile, args.clean)

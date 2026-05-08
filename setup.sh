#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# Trova python3.11 o python3.10, altrimenti usa python3
PYTHON_BIN=""
for ver in python3.11 python3.10 python3; do
    if command -v $ver >/dev/null 2>&1; then
        PYTHON_BIN=$(command -v $ver)
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "Errore: Python 3.10 o 3.11 non trovato. Installa una versione compatibile."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo "Errore: Serve Python >= 3.10. Versione trovata: $PYTHON_VERSION"
    exit 1
fi

echo "Usando Python: $PYTHON_BIN (versione $PYTHON_VERSION)"
$PYTHON_BIN -m venv venv
venv/bin/pip install --upgrade pip
if ! venv/bin/pip install -r requirements.txt; then
    PYTHON_VERSION=$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ "$PYTHON_VERSION" > "3.13" ]]; then
        echo "\n[!] ATTENZIONE: Se l'errore riguarda psycopg2-binary e Python >=3.14, installa anche libpq-dev (Ubuntu/Debian) o postgresql-devel (Fedora):"
        echo "    sudo apt install libpq-dev"
        echo "    # oppure"
        echo "    sudo dnf install postgresql-devel"
    fi
    exit 1
fi

echo "Setup completato. Tutte le dipendenze sono ora in requirements.txt unificato."
echo "Avviso: Python 3.14 è molto recente e alcune librerie potrebbero non essere ancora compatibili (es. python-dotenv, pyinstaller, psycopg2-binary). Se incontri problemi, prova con Python 3.11."
echo "Avvia con: venv/bin/python run_desktop.py oppure venv/bin/python main.py"

venv/bin/python run_desktop.py

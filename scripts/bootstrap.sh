#!/bin/zsh
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "B² Photo Manager – Setup"

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Fehler: python3.12 wurde nicht gefunden."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Erstelle .venv mit Python 3.12 ..."
  python3.12 -m venv .venv
fi

source .venv/bin/activate

PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "$PYTHON_VERSION" != "3.12" ]; then
  echo "Fehler: .venv verwendet Python $PYTHON_VERSION statt 3.12."
  exit 1
fi

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

echo
echo "Setup abgeschlossen."
echo "Prüfung startet ..."
"$PROJECT_ROOT/scripts/check.sh"

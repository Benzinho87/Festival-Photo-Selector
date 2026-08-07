#!/bin/bash
set -e

source "$(cd "$(dirname "$0")" && pwd)/common.sh"
cd "$PROJECT_ROOT"

ensure_environment
export_project_pythonpath

echo "B² Photo Manager – Projektprüfung"

echo "1/7 Python"
"$VENV_PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 12); print(sys.version.split()[0])'

echo "2/7 Paketimport"
"$VENV_PYTHON" -c 'import b2_photo_manager; print(b2_photo_manager.__file__)'

echo "3/7 Qt Runtime"
if [[ "$OSTYPE" == darwin* ]]; then
  "$VENV_PYTHON" - <<'PY'
from PySide6.QtWidgets import QApplication
app = QApplication([])
platform = app.platformName()
print("Qt-Plattform:", platform)
assert platform == "cocoa", f"Erwartet cocoa, erhalten: {platform}"
PY
else
  "$VENV_PYTHON" -c 'import PySide6; print("PySide6:", PySide6.__version__)'
fi

echo "4/7 Repository-Hygiene"
BAD_FILES="$(find src tests scripts -type f \( -name '._*' -o -name '* 2.py' -o -name '* 3.py' -o -name '* copy.py' \) -print 2>/dev/null || true)"
if [ -n "$BAD_FILES" ]; then
  echo "Fehler: Verdächtige Dubletten/AppleDouble-Dateien gefunden:"
  echo "$BAD_FILES"
  exit 1
fi
if [ -d "$PROJECT_ROOT/.venv" ]; then
  echo "Fehler: .venv liegt im Repository. Bitte ./scripts/rebuild-env.sh ausführen."
  exit 1
fi
echo "Repository sauber"

echo "5/7 Git-Referenzen"
if [ -d .git/refs ]; then
  GIT_DUPLICATES="$(find .git/refs -type f \( -name '* 2' -o -name '* 3' -o -name '* 2.lock' -o -name '* 3.lock' \) -print 2>/dev/null || true)"
  if [ -n "$GIT_DUPLICATES" ]; then
    echo "Fehler: Verdächtige Git-Dubletten gefunden:"
    echo "$GIT_DUPLICATES"
    exit 1
  fi
fi
echo "Git-Referenzen sauber"

echo "6/7 Ruff"
"$VENV_PYTHON" -m ruff check .

echo "7/7 Pytest"
"$VENV_PYTHON" -m pytest

echo
echo "Alle Prüfungen bestanden."

#!/bin/zsh
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

echo "B² Photo Manager – Projektprüfung"

if [ ! -x ".venv/bin/python" ]; then
  echo "Fehler: .venv fehlt. Bitte zuerst ./scripts/bootstrap.sh ausführen."
  exit 1
fi

source .venv/bin/activate

echo "1/6 Python"
python -c '
import sys
assert sys.version_info[:2] == (3, 12), sys.version
print(sys.version.split()[0])
'

echo "2/6 Paketimport"
python -c '
import b2_photo_manager
print(b2_photo_manager.__file__)
'

echo "3/6 PySide6 / Cocoa"
python -c '
from pathlib import Path
import PySide6

root = Path(PySide6.__file__).resolve().parent
candidates = [
    root / "Qt" / "plugins" / "platforms" / "libqcocoa.dylib",
    root / "plugins" / "platforms" / "libqcocoa.dylib",
]

existing = [path for path in candidates if path.exists()]
assert existing, "libqcocoa.dylib wurde nicht gefunden"
print(existing[0])
'

echo "4/6 Dubletten"
DUPLICATES="$(find src tests -type f \( -name "* 2.py" -o -name "* 3.py" -o -name "* copy.py" \) 2>/dev/null || true)"

if [ -n "$DUPLICATES" ]; then
  echo "Fehler: Verdächtige Dateidubletten gefunden:"
  echo "$DUPLICATES"
  exit 1
fi

echo "Keine Dubletten gefunden"

echo "5/6 Ruff"
ruff check .

echo "6/6 Pytest"
pytest

echo
echo "Alle Prüfungen bestanden."

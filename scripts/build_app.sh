#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="B² Photo Manager"
VENV_DIR="${B2_PACKAGING_VENV:-$HOME/Library/Caches/B2 Photo Manager/packaging-venv}"

cd "$PROJECT_ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Fehler: macOS-App-Bundles können nur auf macOS gebaut werden."
  exit 1
fi

if [ -d "$PROJECT_ROOT/.venv" ]; then
  echo "Fehler: .venv liegt im Repository. Packaging nutzt eine externe Umgebung."
  exit 1
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Erstelle externe Packaging-Umgebung: $VENV_DIR"
  python3.12 -m venv "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"

"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r requirements-dev.txt
"$PYTHON" -m pip install .

if [ -e "$PROJECT_ROOT/build" ]; then
  chflags -R nouchg "$PROJECT_ROOT/build" 2>/dev/null || true
  rm -rf "$PROJECT_ROOT/build"
fi
if [ -e "$PROJECT_ROOT/dist/$APP_NAME.app" ]; then
  chflags -R nouchg "$PROJECT_ROOT/dist/$APP_NAME.app" 2>/dev/null || true
  rm -rf "$PROJECT_ROOT/dist/$APP_NAME.app"
fi
mkdir -p "$PROJECT_ROOT/dist"
find "$PROJECT_ROOT/dist" -maxdepth 1 -type f -name "$APP_NAME-*.dmg" -delete

"$PYTHON" -m PyInstaller \
  --clean \
  --noconfirm \
  --distpath "$PROJECT_ROOT/dist" \
  --workpath "$PROJECT_ROOT/build" \
  "$PROJECT_ROOT/packaging/macos/b2_photo_manager.spec"

"$SCRIPT_DIR/verify_app.sh" "$PROJECT_ROOT/dist/$APP_NAME.app"

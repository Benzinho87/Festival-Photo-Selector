#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_PATH="${1:-$PROJECT_ROOT/dist/B² Photo Manager.app}"
APP_NAME="B² Photo Manager"
EXECUTABLE="$APP_PATH/Contents/MacOS/$APP_NAME"
PLIST="$APP_PATH/Contents/Info.plist"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Fehler: macOS-Bundles können nur auf macOS geprüft werden."
  exit 1
fi

if [ ! -d "$APP_PATH" ]; then
  echo "Fehler: App-Bundle fehlt: $APP_PATH"
  exit 1
fi

if [ ! -x "$EXECUTABLE" ]; then
  echo "Fehler: Ausführbares Binary fehlt: $EXECUTABLE"
  exit 1
fi

BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$PLIST")"
VERSION="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$PLIST")"
DISPLAY_NAME="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleDisplayName' "$PLIST")"

if [ "$BUNDLE_ID" != "de.bsquared.b2photomanager" ]; then
  echo "Fehler: Unerwarteter Bundle-Identifier: $BUNDLE_ID"
  exit 1
fi

if [ "$DISPLAY_NAME" != "$APP_NAME" ]; then
  echo "Fehler: Unerwarteter App-Name: $DISPLAY_NAME"
  exit 1
fi

REPO_VERSION="$(
  cd "$PROJECT_ROOT"
  python3 - <<'PY'
from pathlib import Path
import tomllib
print(tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])
PY
)"

if [ "$VERSION" != "$REPO_VERSION" ]; then
  echo "Fehler: Bundle-Version $VERSION passt nicht zu Projektversion $REPO_VERSION."
  exit 1
fi

SMOKE_HOME="$(mktemp -d)"
SMOKE_LOG="$SMOKE_HOME/packaging-smoke.json"
HOME="$SMOKE_HOME" "$EXECUTABLE" --packaging-smoke > "$SMOKE_LOG"

if ! grep -q '"qt_platform": "cocoa"' "$SMOKE_LOG"; then
  echo "Fehler: Qt/Cocoa-Smoke-Test fehlgeschlagen."
  cat "$SMOKE_LOG"
  exit 1
fi

for path in \
  "$SMOKE_HOME/Library/Application Support/B2 Photo Manager" \
  "$SMOKE_HOME/Library/Caches/B2 Photo Manager" \
  "$SMOKE_HOME/Library/Logs/B2 Photo Manager"; do
  if [ ! -d "$path" ]; then
    echo "Fehler: Runtime-Pfad wurde nicht angelegt: $path"
    exit 1
  fi
done

open "$APP_PATH"
sleep 3
osascript -e 'tell application "B² Photo Manager" to quit' >/dev/null 2>&1 || true

echo "Bundle geprüft: $APP_PATH"
echo "Version: $VERSION"
echo "Smoke-Test: $SMOKE_LOG"

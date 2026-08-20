#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="B² Photo Manager"
APP_PATH="$PROJECT_ROOT/dist/$APP_NAME.app"
STAGING_DIR="$PROJECT_ROOT/build/dmg"
VERSION="$(
  cd "$PROJECT_ROOT"
  python3 - <<'PY'
from pathlib import Path
import tomllib
print(tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])
PY
)"
DMG_PATH="$PROJECT_ROOT/dist/$APP_NAME-$VERSION.dmg"
VOLUME_NAME="$APP_NAME $VERSION"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Fehler: DMGs können nur auf macOS gebaut werden."
  exit 1
fi

"$SCRIPT_DIR/build_app.sh"

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp -R "$APP_PATH" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"
rm -f "$DMG_PATH"

hdiutil create \
  -volname "$VOLUME_NAME" \
  -srcfolder "$STAGING_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

MOUNT_OUTPUT="$(hdiutil attach "$DMG_PATH" -nobrowse -noautoopen)"
MOUNT_POINT="$(printf '%s\n' "$MOUNT_OUTPUT" | awk '/\/Volumes\// {print substr($0, index($0, "/Volumes/"))}' | tail -n 1)"
if [ -z "$MOUNT_POINT" ] || [ ! -d "$MOUNT_POINT/$APP_NAME.app" ]; then
  echo "Fehler: DMG konnte nicht korrekt geprüft werden."
  printf '%s\n' "$MOUNT_OUTPUT"
  exit 1
fi
hdiutil detach "$MOUNT_POINT" >/dev/null

echo "DMG erstellt: $DMG_PATH"

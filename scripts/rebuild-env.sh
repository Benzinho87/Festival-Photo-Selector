#!/bin/bash
set -e

source "$(cd "$(dirname "$0")" && pwd)/common.sh"
cd "$PROJECT_ROOT"

if [ -d "$PROJECT_ROOT/.venv" ]; then
  echo "Entferne alte virtuelle Umgebung aus dem Repository ..."
  rm -rf "$PROJECT_ROOT/.venv"
fi

rm -rf "$VENV_DIR"
create_environment

echo
echo "Umgebung neu erstellt."
echo "Virtuelle Umgebung: $VENV_DIR"
"$PROJECT_ROOT/scripts/check.sh"

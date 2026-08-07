#!/bin/bash
set -e

source "$(cd "$(dirname "$0")" && pwd)/common.sh"
cd "$PROJECT_ROOT"

echo "B² Photo Manager – Setup"
ensure_environment

echo
echo "Setup abgeschlossen."
echo "Virtuelle Umgebung: $VENV_DIR"
echo "Die Umgebung liegt absichtlich NICHT im Repository."
echo
"$PROJECT_ROOT/scripts/check.sh"

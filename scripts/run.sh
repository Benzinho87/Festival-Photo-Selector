#!/bin/bash
set -e

source "$(cd "$(dirname "$0")" && pwd)/common.sh"
cd "$PROJECT_ROOT"

ensure_environment
export_project_pythonpath
exec "$VENV_PYTHON" "$PROJECT_ROOT/app.py"

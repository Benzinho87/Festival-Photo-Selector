#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${B2_VENV_DIR:-$HOME/.local/share/b2-photo-manager/venv}"
VENV_PYTHON="$VENV_DIR/bin/python"
REQUIREMENTS_STAMP="$VENV_DIR/.b2-requirements.sha256"

resolve_python312() {
  if [ -n "${B2_PYTHON:-}" ] && [ -x "$B2_PYTHON" ]; then
    echo "$B2_PYTHON"
    return 0
  fi

  local framework_python="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
  if [ -x "$framework_python" ]; then
    echo "$framework_python"
    return 0
  fi

  if command -v python3.12 >/dev/null 2>&1; then
    command -v python3.12
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    local candidate="$(command -v python3)"
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null; then
      echo "$candidate"
      return 0
    fi
  fi

  return 1
}

requirements_hash() {
  (cd "$PROJECT_ROOT" && shasum -a 256 requirements.txt requirements-dev.txt | shasum -a 256 | awk '{print $1}')
}

qt_smoke_test() {
  [ -x "$VENV_PYTHON" ] || return 1

  if [[ "$OSTYPE" == darwin* ]]; then
    "$VENV_PYTHON" - <<'PY' >/dev/null 2>&1
from PySide6.QtWidgets import QApplication
app = QApplication([])
raise SystemExit(0 if app.platformName() == "cocoa" else 1)
PY
  else
    "$VENV_PYTHON" -c 'import PySide6' >/dev/null 2>&1
  fi
}

create_environment() {
  local base_python
  base_python="$(resolve_python312)" || {
    echo "Fehler: Python 3.12 wurde nicht gefunden."
    echo "Installiere Python 3.12 oder setze B2_PYTHON auf den Interpreter."
    return 1
  }

  echo "Erstelle isolierte Entwicklungsumgebung außerhalb des Repositories:"
  echo "  $VENV_DIR"
  rm -rf "$VENV_DIR"
  mkdir -p "$(dirname "$VENV_DIR")"
  "$base_python" -m venv "$VENV_DIR"
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -r "$PROJECT_ROOT/requirements-dev.txt"
  requirements_hash > "$REQUIREMENTS_STAMP"
}

ensure_environment() {
  local expected_hash
  expected_hash="$(requirements_hash)"

  local needs_rebuild=0
  if [ ! -x "$VENV_PYTHON" ]; then
    needs_rebuild=1
  elif ! "$VENV_PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' >/dev/null 2>&1; then
    needs_rebuild=1
  elif [ ! -f "$REQUIREMENTS_STAMP" ] || [ "$(cat "$REQUIREMENTS_STAMP")" != "$expected_hash" ]; then
    needs_rebuild=1
  elif ! qt_smoke_test; then
    echo "Die vorhandene Qt-Umgebung ist beschädigt. Sie wird automatisch neu erstellt."
    needs_rebuild=1
  fi

  if [ "$needs_rebuild" -eq 1 ]; then
    create_environment
    qt_smoke_test || {
      echo "Fehler: Qt konnte auch nach einem Neuaufbau nicht gestartet werden."
      return 1
    }
  fi
}

export_project_pythonpath() {
  export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
}

# B² Photo Manager

Stabile Basisversion für macOS.

## v0.1.0
- Python 3.12
- PySide6 6.8.3
- Fotoordner auswählen
- JPG/JPEG/PNG/WebP rekursiv laden
- asynchrone Thumbnails
- Auswahl per Klick
- Auswahlzähler
- Alles auswählen / Auswahl aufheben
- Original per Doppelklick öffnen
- Logging und Tests

## Installation
```bash
brew install python@3.12
cd "/Users/benz/Documents/GitHub/Festival Photo Selector"
rm -rf .venv
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python app.py
```

Tests: `pytest`
Codeprüfung: `ruff check .`

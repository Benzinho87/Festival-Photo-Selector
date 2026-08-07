# B² Photo Manager

Desktop photo selection workflow for event and product photography.

## Current version

v0.2.0

## Features

- Recursive photo folder import
- Asynchronous thumbnails
- Manual selection
- Large photo viewer
- Keyboard navigation
- Fit / 100% / 200% zoom
- Selection directly from viewer

## Development setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check .
python app.py
```

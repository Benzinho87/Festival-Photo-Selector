# B² Photo Manager

## Version 0.2.1.1 – Development Stability

This release adds no new user-facing features. It stabilizes the local macOS development environment.

### What is included

- Automatic Qt/Cocoa platform-plugin detection
- Python 3.12 guard
- `scripts/bootstrap.sh` for a clean local setup
- `scripts/check.sh` for repeatable validation before commits
- Duplicate-file detection for common Finder copies such as `file 2.py`
- Fixed `src/` package layout
- Existing v0.2.1 browser and viewer functionality

### First setup

```bash
chmod +x scripts/bootstrap.sh scripts/check.sh
./scripts/bootstrap.sh
```

### Daily validation

```bash
./scripts/check.sh
```

### Start the app

```bash
source .venv/bin/activate
python app.py
```

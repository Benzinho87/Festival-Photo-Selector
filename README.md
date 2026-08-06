# Festival Photo Selector

Desktop-Anwendung für macOS zur Vorsortierung, Auswahl und Web-Optimierung von Festivalfotos.

## Aktueller Stand

Phase 1 enthält:

- saubere Projektstruktur
- startbare PySide6-Anwendung
- zentrale Konfiguration
- vorbereitete Module für Bildanalyse, Auswahl und Export
- Git-freundliche Ordnerstruktur

## Installation

```bash
cd "/Pfad/zu/Festival-Photo-Selector"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Start

```bash
python app.py
```

## Geplante nächste Schritte

1. Fotoordner auswählen
2. Vorschaubilder laden
3. Fotos markieren und abwählen
4. Auswahl speichern
5. Web-Export mit Größenreduktion und konsistenter Benennung
6. automatische Qualitätsbewertung und Ähnlichkeitserkennung

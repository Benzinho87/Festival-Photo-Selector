# B² Photo Manager

## Version 0.3.0 – professioneller Viewer

B² Photo Manager ist eine lokale Desktop-Anwendung für die schnelle Sichtung, Auswahl und spätere Aufbereitung großer Fotoordner.

### Enthalten

- rekursives Einlesen von Fotoordnern
- responsive Galerie mit Thumbnails
- Auswahl / Abwahl von Fotos
- Filter: Alle, Ausgewählt, Nicht ausgewählt, Favoriten
- Favoriten per Stern
- mehrere Tags pro Foto
- Tag-Filter, kombinierbar mit dem Statusfilter
- aufgeräumter großer Viewer mit Pfeiltasten-Navigation
- sichtbare EXIF-Basisdaten inklusive Fotograf/Autor, Kamera und Aufnahmedaten
- Dateiname, Abmessungen und Dateigröße im Viewer
- Zoom per Fit, 100 %, 200 % sowie Mausrad/Trackpad
- synchroner Auswahl- und Favoritenstatus zwischen Viewer und Übersicht
- reproduzierbare Python-3.12-/PySide6-6.10.3-Umgebung
- echte Qt/Cocoa-Prüfung vor jedem Testlauf

## Entwicklungsumgebung

Die virtuelle Umgebung liegt absichtlich **außerhalb des Repositories**:

```text
~/.local/share/b2-photo-manager/venv
```

Dadurch können iCloud/Finder/Git-Kopierkonflikte im Projektordner die Qt-Binärdateien nicht mehr beschädigen.

Es wird **kein `pip install -e`** verwendet. Der lokale Code wird über `PYTHONPATH=src` gestartet.

## Einmaliges Setup

```bash
chmod +x scripts/*.sh
./scripts/bootstrap.sh
```

## App starten

```bash
./scripts/run.sh
```

Das Skript prüft die Umgebung. Ist sie beschädigt oder haben sich Abhängigkeiten geändert, wird sie automatisch neu erstellt.

## Vor jedem Commit

```bash
./scripts/check.sh
```

Der Check prüft:

1. Python 3.12
2. Paketimport aus `src`
3. echte Qt-/Cocoa-Initialisierung auf macOS
4. Repository-Hygiene / Finder-Dubletten
5. verdächtige Git-Referenz-Dubletten
6. Ruff
7. Pytest

Nur wenn alle Prüfungen grün sind, wird committed.

## Umgebung gezielt neu bauen

```bash
./scripts/rebuild-env.sh
```

Das entfernt auch eine eventuell noch vorhandene alte `.venv` aus dem Repository und baut die externe Umgebung neu auf.

## Arbeitsweise

- Ein Feature = ein Commit.
- Vor jedem Commit: `./scripts/check.sh`.
- Keine kompletten Projektordner über bestehende Ordner kopieren.
- Keine `.venv` in Git oder im Projektordner.
- Änderungen werden als Git-Patch oder über Git vorgenommen.
- Das Repository sollte möglichst nicht in einem durch iCloud synchronisierten `Documents`-Ordner liegen.

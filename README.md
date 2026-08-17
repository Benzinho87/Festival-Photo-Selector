# B² Photo Manager

## Version 0.6.1 – Project Management, Auto-Save & Recovery

B² Photo Manager ist eine lokale Desktop-Anwendung für die schnelle Sichtung,
AI-gestützte Auswahl, Review und den Export großer Fotoordner.

### Enthalten

- rekursives Einlesen von Fotoordnern
- echte Projektdateien im Format `.b2project`
- Projekt öffnen, speichern und speichern unter
- Auto-Save mit Recovery-Datei und Backup der letzten gültigen Projektversion
- Recent-Projects-Liste unter `~/Library/Application Support/B2 Photo Manager/`
- robuste Behandlung fehlender oder verschobener Bilddateien
- responsive Galerie mit skalierbaren Thumbnails
- Auswahl / Abwahl von Fotos
- Filter für Auswahl, Favoriten, AI-Auswahl, Reviewstatus, manuelle Änderungen und Serien
- Favoriten per Stern
- mehrere Tags pro Foto
- Tag-Filter, kombinierbar mit dem Statusfilter
- großer Viewer mit Pfeiltasten-Navigation, Zoom und EXIF-Basisdaten
- AI Selection mit technischem Score, Ästhetik, People-Heuristik und Inhalts-Fingerprints
- stärkere Unterdrückung fast identischer AI-Auswahlbilder
- Review-Modus nur für AI-ausgewählte Fotos
- Reviewstatus, Serienrang, Auswahlgrund und manuelle Korrekturen
- Exportdialog mit Qualitätswarnungen vor dem Export
- reproduzierbare Python-3.12-/PySide6-6.10.3-Umgebung
- echte Qt/Cocoa-Prüfung vor jedem Testlauf

## Entwicklungsumgebung

Die virtuelle Umgebung liegt absichtlich **außerhalb des Repositories**:

```text
~/.local/share/b2-photo-manager/venv
```

Dadurch können iCloud/Finder/Git-Kopierkonflikte im Projektordner die
Qt-Binärdateien nicht mehr beschädigen.

Es wird **kein `pip install -e`** verwendet. Der lokale Code wird über
`PYTHONPATH=src` gestartet.

## Einmaliges Setup

```bash
chmod +x scripts/*.sh
./scripts/bootstrap.sh
```

## App starten

```bash
./scripts/run.sh
```

Das Skript prüft die Umgebung. Ist sie beschädigt oder haben sich
Abhängigkeiten geändert, wird sie automatisch neu erstellt.

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

Das entfernt auch eine eventuell noch vorhandene alte `.venv` aus dem
Repository und baut die externe Umgebung neu auf.

## Projektworkflow

1. Neues Projekt / Fotoordner öffnen
2. Projektdatei `.b2project` speichern
3. AI-Auswahl starten
4. AI-ausgewählte Fotos im Review-Modus prüfen
5. Tags, Favoriten und manuelle Korrekturen setzen
6. Export mit Qualitätscheck öffnen
7. Projekt später wieder öffnen und exakt weiterarbeiten

## Arbeitsweise

- Ein Feature = ein Commit.
- Vor jedem Commit: `./scripts/check.sh`.
- Keine kompletten Projektordner über bestehende Ordner kopieren.
- Keine `.venv` in Git oder im Projektordner.
- Keine manuellen Qt-Plugin-Pfade.
- Start ausschließlich über `scripts/run.sh`.

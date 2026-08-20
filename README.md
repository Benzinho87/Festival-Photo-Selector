# B² Photo Manager

## Version 0.7.1 – macOS DMG Packaging

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
- Serienvergleich für erkannte AI-Serien mit AI-Score, Rang, Favorit, Fit und 100-%-Zoom
- Seriengewinner per Klick oder Taste 1–4, gespeichert als Undo-/Redo-fähiger `series_override`
- bewusste Mehrfachauswahl innerhalb einer Serie bleibt möglich
- erklärbarer Qualitätscheck vor dem Export mit gruppierten Ursachen, betroffenen Fotos und Aktionen
- direkte Navigation aus Qualitätswarnungen zum Bild oder zur betroffenen Serie
- intuitiver Exportdialog mit Auswahl, Bildgröße, Dateien & Ziel
- Exportgröße wahlweise Originalgröße oder maximale Breite/Höhe ohne Hochskalierung
- Live-Beispielanzeige und Zusammenfassung vor dem Export
- Presets für Website, Social Media, E-Mail / klein, Original und Benutzerdefiniert
- Konfliktbehandlung für vorhandene Dateien mit automatischem Umbenennen oder Überspringen
- Exportabschluss mit Anzahl, Fehlern, übersprungenen Dateien, Gesamtgröße und Zielordner
- kompakte Export-Historie im Projekt
- Runtime-Daten außerhalb des Repositories unter macOS-Library-Pfaden
- zentrale Resource-Auflösung über `b2_photo_manager.resources.resource_path()`
- eindeutiger Startpunkt über `b2_photo_manager.cli.main()`
- rotierende Logdatei und Diagnoseansicht für Support/Packaging
- Schutz vor veralteten Worker-Rückmeldungen nach Projektwechsel
- reproduzierbare Python-3.12-/PySide6-6.10.3-Umgebung
- echte Qt/Cocoa-Prüfung vor jedem Testlauf
- reproduzierbares macOS-App-Bundle über PyInstaller
- lokales DMG mit App-Bundle und Applications-Link

## Runtime-Datenorte

Projektdateien `.b2project` bleiben an dem Ort, den du beim Speichern auswählst.
Runtime-Daten werden nicht im Repository abgelegt.

```text
~/Library/Application Support/B2 Photo Manager/
  recent-projects.json
  recovery/
  settings/

~/Library/Caches/B2 Photo Manager/
  ai/
  thumbnails/

~/Library/Logs/B2 Photo Manager/
  b2-photo-manager.log
```

Exportziele bleiben frei wählbar. Als Vorschlag nutzt die App
`~/Pictures/B2 Photo Manager Exports`.

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

## macOS-App bauen

```bash
./scripts/build_app.sh
```

Das erzeugt ein lokal startbares Bundle unter:

```text
dist/B² Photo Manager.app
```

Die Packaging-Umgebung liegt außerhalb des Repositories. Der Build nutzt
PyInstaller, bündelt Python, PySide6, die benötigten Qt-Plugins und Paket-Assets
und startet anschließend `scripts/verify_app.sh`.

Weitere Details stehen in `packaging/macos/README.md`.

## macOS-DMG bauen

```bash
./scripts/build_dmg.sh
```

Das erzeugt nach einem frischen App-Build:

```text
dist/B² Photo Manager-0.7.1.dmg
```

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
6. Versionskonsistenz
7. keine Runtime-Artefakte im Repository
8. Packaging-Vorbedingungen: keine manuellen Qt-Plugin-Pfade, keine relativen Runtime-Pfade
9. Ruff
10. Pytest

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
6. Serien vergleichen
7. Export mit Qualitätscheck öffnen
8. Projekt später wieder öffnen und exakt weiterarbeiten

## Release-Checkliste

1. `./scripts/check.sh`
2. Smoke-Test: Start, Projekt öffnen, AI-Auswahl, Review, Serienvergleich, Qualitätscheck, Export
3. Version in App, Paket und README prüfen
4. Git-Status prüfen
5. Sicherstellen, dass keine Runtime-Daten committed werden

## Arbeitsweise

- Ein Feature = ein Commit.
- Vor jedem Commit: `./scripts/check.sh`.
- Keine kompletten Projektordner über bestehende Ordner kopieren.
- Keine `.venv` in Git oder im Projektordner.
- Keine manuellen Qt-Plugin-Pfade.
- In der Entwicklung über `scripts/run.sh` starten.
- Für spätere `.app`-Bundles darf Code nicht annehmen, dass `src/`, `cache/`
  oder Repository-Dateien neben der App liegen.
- Assets immer über `b2_photo_manager.resources.resource_path()` auflösen.

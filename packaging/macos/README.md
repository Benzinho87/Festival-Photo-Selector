# macOS Packaging

## Ziel

`./scripts/build_app.sh` erzeugt ein lokal startbares App-Bundle:

```text
dist/B² Photo Manager.app
```

Das Bundle wird mit PyInstaller gebaut, startet ohne Terminalfenster und enthält Python,
PySide6, die benötigten Qt-Plugins und die Paket-Assets.

## Voraussetzungen

- macOS
- Python 3.12
- Internetzugang beim ersten Erstellen der externen Packaging-Umgebung

Die Build-Umgebung liegt außerhalb des Repositories. Standard:

```text
~/Library/Caches/B2 Photo Manager/packaging-venv
```

Mit `B2_PACKAGING_VENV=/pfad/zur/venv` kann ein anderer Ort gewählt werden.

## Build

```bash
./scripts/build_app.sh
```

Das Skript installiert Runtime-, Dev- und Packaging-Abhängigkeiten in die externe
Build-Umgebung, setzt `build/` und `dist/` zurück, führt PyInstaller aus und startet
anschließend `./scripts/verify_app.sh`.

## DMG

```bash
./scripts/build_dmg.sh
```

Das Skript baut zuerst ein frisches App-Bundle und erzeugt danach:

```text
dist/B² Photo Manager-0.7.1.dmg
```

Der Inhalt des DMG ist bewusst schlicht:

```text
B² Photo Manager.app
Applications -> /Applications
```

Zum Abschluss wird das DMG gemountet, der App-Inhalt geprüft und wieder ausgehängt.

## Lokaler Test

Nach erfolgreichem Build:

```bash
open "dist/B² Photo Manager.app"
```

`verify_app.sh` prüft zusätzlich das Bundle, die Metadaten, den ausführbaren Startpunkt,
Qt/Cocoa, zentrale Imports, Resource-Auflösung und Runtime-Pfade außerhalb der App.

## App-Icon

Wenn `assets/icon.icns` existiert, bindet die Spec es automatisch ein. Aktuell wird kein
generisches Icon erzeugt.

## Einschränkungen

v0.7.1 ist ein lokaler, unsigned Build. Developer-ID-Signing, Hardened Runtime,
Notarisierung und Gatekeeper-Tests auf fremden Macs sind nicht Teil dieses Releases.

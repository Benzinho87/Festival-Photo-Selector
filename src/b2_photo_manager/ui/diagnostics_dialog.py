import platform
import sys

import PySide6
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from b2_photo_manager import __version__
from b2_photo_manager.config import CONFIG
from b2_photo_manager.runtime_paths import runtime_paths
from b2_photo_manager.services.project import PROJECT_FORMAT_VERSION


class DiagnosticsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnoseinformationen")
        self.resize(640, 420)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(diagnostics_text())

        close_button = QPushButton("Schließen")
        close_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Technische Informationen für Fehlersuche und Packaging."))
        layout.addWidget(text, 1)
        layout.addWidget(close_button)


def diagnostics_text() -> str:
    paths = runtime_paths()
    return "\n".join(
        [
            f"{CONFIG.app_name} {__version__}",
            f"Betriebssystem: {platform.platform()}",
            f"Python: {sys.version.split()[0]}",
            f"PySide6: {PySide6.__version__}",
            f"Projektformat: {PROJECT_FORMAT_VERSION}",
            f"App-Daten: {paths.app_support}",
            f"Cache: {paths.cache}",
            f"Logs: {paths.logs}",
        ]
    )

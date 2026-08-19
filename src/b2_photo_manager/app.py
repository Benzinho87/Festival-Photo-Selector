import sys

from PySide6.QtWidgets import QApplication

from b2_photo_manager.logging_setup import log_runtime_paths, setup_logging
from b2_photo_manager.ui.main_window import MainWindow


def run() -> None:
    setup_logging()
    log_runtime_paths()

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    raise SystemExit(app.exec())

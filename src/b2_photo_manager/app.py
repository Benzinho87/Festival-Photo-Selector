import logging
import sys
from PySide6.QtWidgets import QApplication
from b2_photo_manager.config import CONFIG
from b2_photo_manager.logging_setup import configure_logging
from b2_photo_manager.ui.main_window import MainWindow

LOGGER = logging.getLogger(__name__)

def run() -> int:
    configure_logging()
    LOGGER.info("Starting %s %s", CONFIG.app_name, CONFIG.version)
    app = QApplication(sys.argv)
    app.setApplicationName(CONFIG.app_name)
    app.setApplicationVersion(CONFIG.version)
    app.setOrganizationName("B Squared Media")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()

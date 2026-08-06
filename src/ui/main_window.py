import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config import CONFIG


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{CONFIG.app_name} {CONFIG.version}")
        self.resize(960, 640)

        title = QLabel(CONFIG.app_name)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 600;")

        status = QLabel("Phase 1 ist eingerichtet. Die Fotoauswahl folgt in Phase 2.")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        close_button = QPushButton("Schließen")
        close_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(status)
        layout.addSpacing(24)
        layout.addWidget(close_button)
        layout.addStretch()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


def run_app() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QGridLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QToolBar, QVBoxLayout, QWidget
)
from src.config import CONFIG
from src.models.photo import Photo
from src.ui.photo_card import PhotoCard
from src.ui.preview_dialog import PreviewDialog
from src.ui.export_dialog import ExportDialog
from src.utils.files import find_images

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.photos = []
        self.cards = {}
        self.setWindowTitle(f"{CONFIG.app_name} {CONFIG.version}")
        self.resize(1200, 820)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        open_action = QAction("Fotoordner auswählen", self)
        open_action.triggered.connect(self.choose_folder)
        toolbar.addAction(open_action)

        export_action = QAction("Exportieren", self)
        export_action.triggered.connect(self.open_export_dialog)
        toolbar.addAction(export_action)

        self.summary = QLabel("Noch kein Ordner geladen")
        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.grid_widget)

        layout = QVBoxLayout()
        layout.addWidget(self.summary)
        layout.addWidget(scroll)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def choose_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "Fotoordner auswählen", str(Path.home() / "Pictures"))
        if not selected:
            return
        paths = find_images(Path(selected))
        if not paths:
            QMessageBox.information(self, "Keine Fotos", "Keine unterstützten Bilder gefunden.")
            return
        self.load_photos(paths)

    def load_photos(self, paths):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.photos = [Photo(path=p) for p in paths]
        self.cards = {}

        for i, photo in enumerate(self.photos):
            card = PhotoCard(photo)
            card.selection_changed.connect(self.update_summary)
            card.preview_requested.connect(self.open_preview)
            self.cards[photo.path] = card
            self.grid.addWidget(card, i // CONFIG.thumbnail_columns, i % CONFIG.thumbnail_columns)

            pixmap = QPixmap(str(photo.path))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    CONFIG.thumbnail_width,
                    CONFIG.thumbnail_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                card.set_thumbnail(pixmap)

        self.update_summary()

    def update_summary(self, *_):
        selected = sum(p.selected for p in self.photos)
        self.summary.setText(f"{selected} ausgewählt · {len(self.photos)} Fotos")
        for p in self.photos:
            if p.path in self.cards:
                self.cards[p.path].refresh_style()

    def open_preview(self, path):
        index = next((i for i, p in enumerate(self.photos) if p.path == path), 0)
        dialog = PreviewDialog(self.photos, index, self)
        dialog.selection_changed.connect(self.update_summary)
        dialog.exec()

    def open_export_dialog(self):
        if not any(p.selected for p in self.photos):
            QMessageBox.information(self, "Keine Auswahl", "Wähle zuerst mindestens ein Foto aus.")
            return
        ExportDialog(self.photos, self).exec()

def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()

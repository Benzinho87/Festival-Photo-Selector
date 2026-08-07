import logging
import subprocess
from pathlib import Path

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtGui import QAction, QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from b2_photo_manager.config import CONFIG
from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.photo_finder import find_photos
from b2_photo_manager.services.thumbnail_service import ThumbnailWorker
from b2_photo_manager.ui.photo_card import PhotoCard

LOGGER = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.photos: list[Photo] = []
        self.cards: dict[Path, PhotoCard] = {}
        self.loaded_count = 0
        self.thread_pool = QThreadPool.globalInstance()

        self.setWindowTitle(f"{CONFIG.app_name} {CONFIG.version}")
        self.resize(1200, 820)

        self._build_toolbar()
        self._build_content()
        self.setStatusBar(QStatusBar())
        self._update_status()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Werkzeuge")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction("Fotoordner auswählen", self)
        open_action.triggered.connect(self.choose_folder)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        select_all_action = QAction("Alles auswählen", self)
        select_all_action.triggered.connect(self.select_all)
        toolbar.addAction(select_all_action)

        clear_action = QAction("Auswahl aufheben", self)
        clear_action.triggered.connect(self.clear_selection)
        toolbar.addAction(clear_action)

    def _build_content(self) -> None:
        self.heading = QLabel(CONFIG.app_name)
        self.heading.setStyleSheet("font-size:26px; font-weight:600;")

        self.summary_label = QLabel("Wähle einen Ordner mit Fotos aus.")

        self.open_button = QPushButton("Fotoordner auswählen")
        self.open_button.clicked.connect(self.choose_folder)

        top = QHBoxLayout()
        top.addWidget(self.heading)
        top.addStretch()
        top.addWidget(self.summary_label)

        controls = QHBoxLayout()
        controls.addWidget(self.open_button)
        controls.addStretch()

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.grid_layout.setHorizontalSpacing(14)
        self.grid_layout.setVerticalSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.grid_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addLayout(top)
        layout.addLayout(controls)
        layout.addWidget(scroll)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Fotoordner auswählen",
            str(CONFIG.default_photo_directory),
        )

        if not selected:
            return

        try:
            paths = find_photos(Path(selected))
        except OSError as exc:
            LOGGER.exception("Could not scan photo folder")
            QMessageBox.warning(
                self,
                "Ordner konnte nicht gelesen werden",
                str(exc),
            )
            return

        if not paths:
            QMessageBox.information(
                self,
                "Keine Fotos gefunden",
                "Keine unterstützten Bilddateien gefunden.",
            )
            return

        LOGGER.info("Loading %d photos from %s", len(paths), selected)
        self.load_photos(paths)

    def load_photos(self, paths: list[Path]) -> None:
        self._clear_grid()

        self.photos = [Photo(path=path) for path in paths]
        self.cards = {}
        self.loaded_count = 0

        for index, photo in enumerate(self.photos):
            card = PhotoCard(photo)
            card.selection_changed.connect(self._on_selection_changed)
            card.open_requested.connect(self._open_original)
            self.cards[photo.path] = card

            row = index // CONFIG.thumbnail_columns
            column = index % CONFIG.thumbnail_columns
            self.grid_layout.addWidget(card, row, column)

            worker = ThumbnailWorker(photo.path)
            worker.signals.loaded.connect(self._on_thumbnail_loaded)
            worker.signals.failed.connect(self._on_thumbnail_failed)
            self.thread_pool.start(worker)

        self._update_status()

    def _clear_grid(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _on_thumbnail_loaded(self, path: Path, image: QImage) -> None:
        card = self.cards.get(path)

        if card is not None:
            card.set_thumbnail(QPixmap.fromImage(image))

        self.loaded_count += 1
        self._update_status()

    def _on_thumbnail_failed(self, path: Path, message: str) -> None:
        LOGGER.warning("Thumbnail failed for %s: %s", path, message)

        card = self.cards.get(path)

        if card is not None:
            card.set_error(message)

        self.loaded_count += 1
        self._update_status()

    def _on_selection_changed(self, photo: Photo) -> None:
        card = self.cards.get(photo.path)

        if card is not None:
            card.refresh_style()

        self._update_status()

    def select_all(self) -> None:
        for photo in self.photos:
            photo.selected = True
            self.cards[photo.path].refresh_style()

        self._update_status()

    def clear_selection(self) -> None:
        for photo in self.photos:
            photo.selected = False
            self.cards[photo.path].refresh_style()

        self._update_status()

    def _open_original(self, path: Path) -> None:
        try:
            subprocess.run(["open", str(path)], check=True)
        except Exception as exc:
            LOGGER.exception("Could not open image")
            QMessageBox.warning(
                self,
                "Bild konnte nicht geöffnet werden",
                str(exc),
            )

    def _update_status(self) -> None:
        selected = sum(photo.selected for photo in self.photos)
        total = len(self.photos)

        self.summary_label.setText(
            f"{selected} ausgewählt · {total} Fotos"
        )

        if total:
            message = (
                f"Vorschaubilder geladen: "
                f"{self.loaded_count}/{total}"
            )
        else:
            message = "Noch kein Fotoordner geladen"

        self.statusBar().showMessage(message)

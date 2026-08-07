import logging
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QAction, QImage, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QComboBox,
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
from b2_photo_manager.services.gallery_layout import calculate_columns
from b2_photo_manager.services.photo_finder import find_photos
from b2_photo_manager.services.thumbnail_service import ThumbnailWorker
from b2_photo_manager.ui.photo_card import PhotoCard
from b2_photo_manager.ui.preview_dialog import PreviewDialog

LOGGER = logging.getLogger(__name__)

FILTER_ALL = "Alle"
FILTER_SELECTED = "Ausgewählt"
FILTER_UNSELECTED = "Nicht ausgewählt"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.photos: list[Photo] = []
        self.cards: dict[Path, PhotoCard] = {}
        self.loaded_count = 0
        self.current_columns = 0
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
        self.heading.setStyleSheet(
            "font-size: 26px; font-weight: 600;"
        )

        self.summary_label = QLabel(
            "Wähle einen Ordner mit Fotos aus."
        )

        self.open_button = QPushButton("Fotoordner auswählen")
        self.open_button.clicked.connect(self.choose_folder)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(
            [
                FILTER_ALL,
                FILTER_SELECTED,
                FILTER_UNSELECTED,
            ]
        )
        self.filter_combo.currentTextChanged.connect(
            self._apply_filter
        )

        top = QHBoxLayout()
        top.addWidget(self.heading)
        top.addStretch()
        top.addWidget(self.summary_label)

        controls = QHBoxLayout()
        controls.addWidget(self.open_button)
        controls.addStretch()
        controls.addWidget(QLabel("Anzeige:"))
        controls.addWidget(self.filter_combo)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignLeft
        )
        self.grid_layout.setHorizontalSpacing(
            CONFIG.gallery_spacing
        )
        self.grid_layout.setVerticalSpacing(
            CONFIG.gallery_spacing
        )

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.grid_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addLayout(top)
        layout.addLayout(controls)
        layout.addWidget(self.scroll)

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

        LOGGER.info(
            "Loading %d photos from %s",
            len(paths),
            selected,
        )
        self.load_photos(paths)

    def load_photos(self, paths: list[Path]) -> None:
        self._clear_grid()

        self.photos = [
            Photo(path=path)
            for path in paths
        ]
        self.cards = {}
        self.loaded_count = 0
        self.current_columns = 0
        self.filter_combo.setCurrentText(FILTER_ALL)

        for photo in self.photos:
            card = PhotoCard(photo)
            card.selection_changed.connect(
                self._on_selection_changed
            )
            card.open_requested.connect(
                self._open_preview
            )
            self.cards[photo.path] = card

            worker = ThumbnailWorker(photo.path)
            worker.signals.loaded.connect(
                self._on_thumbnail_loaded
            )
            worker.signals.failed.connect(
                self._on_thumbnail_failed
            )
            self.thread_pool.start(worker)

        self._relayout_gallery(force=True)
        self._update_status()

    def _clear_grid(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _visible_photos(self) -> list[Photo]:
        filter_name = self.filter_combo.currentText()

        if filter_name == FILTER_SELECTED:
            return [
                photo
                for photo in self.photos
                if photo.selected
            ]

        if filter_name == FILTER_UNSELECTED:
            return [
                photo
                for photo in self.photos
                if not photo.selected
            ]

        return list(self.photos)

    def _apply_filter(self) -> None:
        self._relayout_gallery(force=True)
        self._update_status()

    def _relayout_gallery(self, force: bool = False) -> None:
        if not self.cards:
            return

        card_width = CONFIG.thumbnail_width + 24
        viewport_width = self.scroll.viewport().width()
        columns = calculate_columns(
            viewport_width=viewport_width,
            card_width=card_width,
            spacing=CONFIG.gallery_spacing,
            minimum=CONFIG.thumbnail_min_columns,
        )

        visible_photos = self._visible_photos()

        if not force and columns == self.current_columns:
            return

        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        for card in self.cards.values():
            card.hide()

        for index, photo in enumerate(visible_photos):
            card = self.cards[photo.path]
            row = index // columns
            column = index % columns
            self.grid_layout.addWidget(
                card,
                row,
                column,
            )
            card.show()

        self.current_columns = columns

    def _on_thumbnail_loaded(
        self,
        path: Path,
        image: QImage,
    ) -> None:
        card = self.cards.get(path)

        if card is not None:
            card.set_thumbnail(
                QPixmap.fromImage(image)
            )

        self.loaded_count += 1
        self._update_status()

    def _on_thumbnail_failed(
        self,
        path: Path,
        message: str,
    ) -> None:
        LOGGER.warning(
            "Thumbnail failed for %s: %s",
            path,
            message,
        )

        card = self.cards.get(path)

        if card is not None:
            card.set_error(message)

        self.loaded_count += 1
        self._update_status()

    def _on_selection_changed(
        self,
        photo: Photo,
    ) -> None:
        card = self.cards.get(photo.path)

        if card is not None:
            card.refresh_style()

        if self.filter_combo.currentText() != FILTER_ALL:
            self._relayout_gallery(force=True)

        self._update_status()

    def _open_preview(self, path: Path) -> None:
        start_index = next(
            (
                index
                for index, photo in enumerate(self.photos)
                if photo.path == path
            ),
            0,
        )

        dialog = PreviewDialog(
            self.photos,
            start_index,
            self,
        )
        dialog.selection_changed.connect(
            self._on_selection_changed
        )
        dialog.exec()

        self._relayout_gallery(force=True)
        self._update_status()

    def select_all(self) -> None:
        for photo in self.photos:
            photo.selected = True
            self.cards[photo.path].refresh_style()

        self._relayout_gallery(force=True)
        self._update_status()

    def clear_selection(self) -> None:
        for photo in self.photos:
            photo.selected = False
            self.cards[photo.path].refresh_style()

        self._relayout_gallery(force=True)
        self._update_status()

    def _update_status(self) -> None:
        selected = sum(
            photo.selected
            for photo in self.photos
        )
        total = len(self.photos)
        visible = len(self._visible_photos()) if total else 0

        self.summary_label.setText(
            f"{total} Fotos · {selected} ausgewählt"
        )

        if total:
            message = (
                f"{visible} sichtbar · "
                f"Vorschaubilder geladen: "
                f"{self.loaded_count}/{total}"
            )
        else:
            message = "Noch kein Fotoordner geladen"

        self.statusBar().showMessage(message)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._relayout_gallery()

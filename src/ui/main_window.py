import subprocess
import sys
from pathlib import Path
from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtGui import QAction, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QScrollArea, QStatusBar, QToolBar, QVBoxLayout, QWidget
from src.config import CONFIG
from src.models.photo import Photo
from src.ui.photo_card import PhotoCard
from src.ui.thumbnail_worker import ThumbnailWorker
from src.utils.files import find_images

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
        self._build_central_widget()
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

    def _build_central_widget(self) -> None:
        self.heading = QLabel("Festival Photo Selector")
        self.heading.setStyleSheet("font-size:26px;font-weight:600;")
        self.summary_label = QLabel("Wähle einen Ordner mit Festivalfotos aus.")
        self.open_button = QPushButton("Fotoordner auswählen")
        self.open_button.clicked.connect(self.choose_folder)
        top_row = QHBoxLayout()
        top_row.addWidget(self.heading)
        top_row.addStretch()
        top_row.addWidget(self.summary_label)
        controls = QHBoxLayout()
        controls.addWidget(self.open_button)
        controls.addStretch()
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setHorizontalSpacing(14)
        self.grid_layout.setVerticalSpacing(14)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.grid_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(18,18,18,18)
        main_layout.addLayout(top_row)
        main_layout.addLayout(controls)
        main_layout.addWidget(scroll_area)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Fotoordner auswählen", str(Path.home()/"Pictures"))
        if not selected:
            return
        paths = find_images(Path(selected))
        if not paths:
            QMessageBox.information(self, "Keine Fotos gefunden", "Im gewählten Ordner wurden keine unterstützten Bilddateien gefunden.")
            return
        self.load_photos(paths)

    def load_photos(self, paths: list[Path]) -> None:
        self._clear_grid()
        self.photos = [Photo(path=p) for p in paths]
        self.cards = {}
        self.loaded_count = 0
        for index, photo in enumerate(self.photos):
            card = PhotoCard(photo)
            card.selection_changed.connect(self._on_selection_changed)
            card.open_requested.connect(self._open_original)
            self.cards[photo.path] = card
            self.grid_layout.addWidget(card, index//CONFIG.thumbnail_columns, index%CONFIG.thumbnail_columns)
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
        card = self.cards.get(path)
        if card is not None:
            card.set_error(message)
        self.loaded_count += 1
        self._update_status()

    def _on_selection_changed(self, _photo: Photo) -> None:
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
            QMessageBox.warning(self, "Bild konnte nicht geöffnet werden", str(exc))

    def _update_status(self) -> None:
        selected_count = sum(p.selected for p in self.photos)
        total_count = len(self.photos)
        self.summary_label.setText(f"{selected_count} ausgewählt · {total_count} Fotos")
        if total_count:
            self.statusBar().showMessage(f"Vorschaubilder geladen: {self.loaded_count}/{total_count}")
        else:
            self.statusBar().showMessage("Noch kein Fotoordner geladen")

def run_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(CONFIG.app_name)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()

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
    QSpinBox,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from b2_photo_manager.config import CONFIG
from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.models import SelectionProfile, SelectionRequest, SelectionTarget
from b2_photo_manager.services.ai.worker import SelectionWorker
from b2_photo_manager.services.gallery_layout import calculate_columns
from b2_photo_manager.services.photo_filter import (
    ALL_TAGS,
    FILTER_AI_SCORE_70,
    FILTER_AI_SELECTED,
    FILTER_AI_UNSELECTED,
    FILTER_ALL,
    FILTER_FAVORITES,
    FILTER_MANUAL_CHANGED,
    FILTER_REVIEW_REVIEWED,
    FILTER_REVIEW_UNREVIEWED,
    FILTER_SELECTED,
    FILTER_SERIES,
    FILTER_UNSELECTED,
    filter_photos,
)
from b2_photo_manager.services.photo_finder import find_photos
from b2_photo_manager.services.review import (
    ReviewHistory,
    apply_series_groups,
    mark_review_decision,
    quality_warnings,
    review_progress,
    save_project_state,
)
from b2_photo_manager.services.thumbnail_service import ThumbnailWorker
from b2_photo_manager.ui.export_dialog import ExportDialog
from b2_photo_manager.ui.photo_card import PhotoCard
from b2_photo_manager.ui.preview_dialog import PreviewDialog
from b2_photo_manager.ui.tag_dialog import TagDialog

LOGGER = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.photos: list[Photo] = []
        self.cards: dict[Path, PhotoCard] = {}
        self.loaded_count = 0
        self.current_columns = 0
        self.thread_pool = QThreadPool.globalInstance()
        self.selection_worker: SelectionWorker | None = None
        self.analysis_running = False
        self.series = ()
        self.manual_corrections = []
        self.history = ReviewHistory()

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
        toolbar.addSeparator()

        export_action = QAction("Exportieren", self)
        export_action.triggered.connect(self.open_export_dialog)
        toolbar.addAction(export_action)
        toolbar.addSeparator()

        review_action = QAction("Review-Modus", self)
        review_action.triggered.connect(self.open_review_mode)
        toolbar.addAction(review_action)

        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.undo)
        toolbar.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.redo)
        toolbar.addAction(redo_action)

    def _build_content(self) -> None:
        self.heading = QLabel(CONFIG.app_name)
        self.heading.setStyleSheet("font-size: 26px; font-weight: 600;")
        self.summary_label = QLabel("Wähle einen Ordner mit Fotos aus.")

        self.open_button = QPushButton("Fotoordner auswählen")
        self.open_button.clicked.connect(self.choose_folder)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(
            [
                FILTER_ALL,
                FILTER_SELECTED,
                FILTER_UNSELECTED,
                FILTER_FAVORITES,
                FILTER_AI_SELECTED,
                FILTER_AI_UNSELECTED,
                FILTER_AI_SCORE_70,
                FILTER_REVIEW_UNREVIEWED,
                FILTER_REVIEW_REVIEWED,
                FILTER_MANUAL_CHANGED,
                FILTER_SERIES,
            ]
        )
        self.filter_combo.currentTextChanged.connect(self._apply_filter)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Dateiname", "AI-Score", "Review-Status", "Aufnahmedatum"])
        self.sort_combo.currentTextChanged.connect(self._apply_filter)

        self.profile_combo = QComboBox()
        self.profile_combo.addItems([profile.value for profile in SelectionProfile])

        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 3000)
        self.target_spin.setValue(80)
        self.target_spin.setSuffix(" Fotos")

        self.ai_button = QPushButton("AI-Auswahl starten")
        self.ai_button.clicked.connect(self.start_ai_selection)

        self.cancel_ai_button = QPushButton("Abbrechen")
        self.cancel_ai_button.clicked.connect(self.cancel_ai_selection)
        self.cancel_ai_button.setEnabled(False)

        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.addItem(ALL_TAGS)
        self.tag_filter_combo.currentTextChanged.connect(self._apply_filter)

        top = QHBoxLayout()
        top.addWidget(self.heading)
        top.addStretch()
        top.addWidget(self.summary_label)

        controls = QHBoxLayout()
        controls.addWidget(self.open_button)
        controls.addStretch()
        controls.addWidget(QLabel("Anzeige:"))
        controls.addWidget(self.filter_combo)
        controls.addWidget(QLabel("Tag:"))
        controls.addWidget(self.tag_filter_combo)
        controls.addWidget(QLabel("Sortierung:"))
        controls.addWidget(self.sort_combo)

        ai_controls = QHBoxLayout()
        ai_controls.addWidget(QLabel("AI-Profil:"))
        ai_controls.addWidget(self.profile_combo)
        ai_controls.addWidget(QLabel("Ziel:"))
        ai_controls.addWidget(self.target_spin)
        ai_controls.addWidget(self.ai_button)
        ai_controls.addWidget(self.cancel_ai_button)
        ai_controls.addStretch()

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setHorizontalSpacing(CONFIG.gallery_spacing)
        self.grid_layout.setVerticalSpacing(CONFIG.gallery_spacing)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.grid_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addLayout(top)
        layout.addLayout(controls)
        layout.addLayout(ai_controls)
        layout.addWidget(self.scroll)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self, "Fotoordner auswählen", str(CONFIG.default_photo_directory)
        )
        if not selected:
            return

        try:
            paths = find_photos(Path(selected))
        except OSError as exc:
            LOGGER.exception("Could not scan photo folder")
            QMessageBox.warning(self, "Ordner konnte nicht gelesen werden", str(exc))
            return

        if not paths:
            QMessageBox.information(
                self, "Keine Fotos gefunden", "Keine unterstützten Bilddateien gefunden."
            )
            return
        self.load_photos(paths)

    def load_photos(self, paths: list[Path]) -> None:
        self._clear_grid()
        self.photos = [Photo(path=path) for path in paths]
        self.cards = {}
        self.loaded_count = 0
        self.current_columns = 0
        self.filter_combo.setCurrentText(FILTER_ALL)

        for photo in self.photos:
            card = PhotoCard(photo)
            card.selection_changed.connect(self._on_photo_changed)
            card.favorite_changed.connect(self._on_photo_changed)
            card.tags_requested.connect(self._edit_tags)
            card.open_requested.connect(self._open_preview)
            self.cards[photo.path] = card

            worker = ThumbnailWorker(photo.path)
            worker.signals.loaded.connect(self._on_thumbnail_loaded)
            worker.signals.failed.connect(self._on_thumbnail_failed)
            self.thread_pool.start(worker)

        self._refresh_tag_filter()
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
        return filter_photos(
            self.photos,
            self.filter_combo.currentText(),
            self.tag_filter_combo.currentText(),
        )

    def _sorted_visible_photos(self) -> list[Photo]:
        photos = self._visible_photos()
        if self.sort_combo.currentText() == "AI-Score":
            return sorted(photos, key=lambda photo: photo.ai_score or -1.0, reverse=True)
        if self.sort_combo.currentText() == "Review-Status":
            return sorted(photos, key=lambda photo: (photo.review_status, photo.path.name))
        if self.sort_combo.currentText() == "Aufnahmedatum":
            return sorted(
                photos,
                key=lambda photo: (
                    photo.path.stat().st_mtime if photo.path.exists() else 0,
                    photo.path.name,
                ),
            )
        return photos

    def _apply_filter(self) -> None:
        self._relayout_gallery(force=True)
        self._update_status()

    def _relayout_gallery(self, force: bool = False) -> None:
        if not self.cards:
            return

        columns = calculate_columns(
            viewport_width=self.scroll.viewport().width(),
            card_width=CONFIG.thumbnail_width + 24,
            spacing=CONFIG.gallery_spacing,
            minimum=CONFIG.thumbnail_min_columns,
        )
        if not force and columns == self.current_columns:
            return

        while self.grid_layout.count():
            self.grid_layout.takeAt(0)
        for card in self.cards.values():
            card.hide()
        for index, photo in enumerate(self._sorted_visible_photos()):
            card = self.cards[photo.path]
            self.grid_layout.addWidget(card, index // columns, index % columns)
            card.show()
        self.current_columns = columns

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

    def _on_photo_changed(self, photo: Photo) -> None:
        card = self.cards.get(photo.path)
        if card is not None:
            card.refresh_style()
        self._refresh_tag_filter()
        self._relayout_gallery(force=True)
        self._update_status()

    def open_review_mode(self) -> None:
        review_photos = [photo for photo in self.photos if photo.ai_selected or photo.selected]
        if not review_photos:
            QMessageBox.information(
                self,
                "Keine AI-Auswahl",
                "Bitte zuerst eine AI-Auswahl starten.",
            )
            return
        dialog = PreviewDialog(review_photos, 0, self)
        dialog.selection_decision_requested.connect(
            lambda photo, keep: mark_review_decision(
                photo, keep, self.manual_corrections, self.history
            )
        )
        dialog.selection_changed.connect(self._on_photo_changed)
        dialog.favorite_changed.connect(self._on_photo_changed)
        dialog.exec()
        self._relayout_gallery(force=True)
        self._update_status()

    def undo(self) -> None:
        photo = self.history.undo()
        if photo is not None:
            self._on_photo_changed(photo)

    def redo(self) -> None:
        photo = self.history.redo()
        if photo is not None:
            self._on_photo_changed(photo)

    def _edit_tags(self, photo: Photo) -> None:
        dialog = TagDialog(photo, self)
        if dialog.exec():
            photo.tags = dialog.parsed_tags()
            self._on_photo_changed(photo)

    def _refresh_tag_filter(self) -> None:
        current = self.tag_filter_combo.currentText() or ALL_TAGS
        tags = sorted({tag for photo in self.photos for tag in photo.tags})
        self.tag_filter_combo.blockSignals(True)
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem(ALL_TAGS)
        self.tag_filter_combo.addItems(tags)
        selected_tag = current if current in tags or current == ALL_TAGS else ALL_TAGS
        self.tag_filter_combo.setCurrentText(selected_tag)
        self.tag_filter_combo.blockSignals(False)

    def _open_preview(self, path: Path) -> None:
        start_index = next(
            (index for index, photo in enumerate(self.photos) if photo.path == path), 0
        )
        dialog = PreviewDialog(self.photos, start_index, self)
        dialog.selection_decision_requested.connect(
            lambda photo, keep: mark_review_decision(
                photo, keep, self.manual_corrections, self.history
            )
        )
        dialog.selection_changed.connect(self._on_photo_changed)
        dialog.favorite_changed.connect(self._on_photo_changed)
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

    def start_ai_selection(self) -> None:
        if not self.photos:
            QMessageBox.information(
                self, "Keine Fotos geladen", "Bitte zuerst einen Fotoordner auswählen."
            )
            return
        if self.analysis_running:
            return

        profile = SelectionProfile(self.profile_combo.currentText())
        request = SelectionRequest(
            profile=profile,
            target=SelectionTarget(count=self.target_spin.value()),
        )
        cache_file = Path("cache") / "ai-analysis-v1.json"
        self.selection_worker = SelectionWorker(self.photos, request, cache_file)
        self.selection_worker.signals.progress.connect(self._on_ai_progress)
        self.selection_worker.signals.finished.connect(self._on_ai_finished)
        self.selection_worker.signals.failed.connect(self._on_ai_failed)
        self.analysis_running = True
        self.ai_button.setEnabled(False)
        self.cancel_ai_button.setEnabled(True)
        self.statusBar().showMessage("AI-Analyse gestartet …")
        self.thread_pool.start(self.selection_worker)

    def cancel_ai_selection(self) -> None:
        if self.selection_worker is not None:
            self.selection_worker.cancel()
        self.cancel_ai_button.setEnabled(False)
        self.statusBar().showMessage("AI-Analyse wird abgebrochen …")

    def _on_ai_progress(self, done: int, total: int, path: Path) -> None:
        name = path.name if path and path.name else "Auswahl wird berechnet"
        self.statusBar().showMessage(f"AI-Analyse: {done}/{total} · {name}")

    def _on_ai_finished(self, summary) -> None:
        self.analysis_running = False
        self.selection_worker = None
        self.ai_button.setEnabled(True)
        self.cancel_ai_button.setEnabled(False)
        for card in self.cards.values():
            card.refresh_style()
        self.series = summary.series
        apply_series_groups(self.photos, summary.series)
        self._relayout_gallery(force=True)
        self._update_status()
        error_note = f" · {len(summary.errors)} Fehler" if summary.errors else ""
        self.statusBar().showMessage(
            f"AI-Auswahl fertig: {len(summary.selected)} Empfehlungen, "
            f"{len(summary.series)} Serien{error_note}"
        )

    def _on_ai_failed(self, message: str) -> None:
        self.analysis_running = False
        self.selection_worker = None
        self.ai_button.setEnabled(True)
        self.cancel_ai_button.setEnabled(False)
        QMessageBox.warning(self, "AI-Analyse fehlgeschlagen", message)

    def open_export_dialog(self) -> None:
        if not self.photos:
            QMessageBox.information(
                self, "Keine Fotos geladen", "Bitte zuerst einen Fotoordner auswählen."
            )
            return
        if not any(photo.selected for photo in self.photos):
            QMessageBox.information(
                self, "Keine Auswahl", "Bitte zuerst Fotos für den Export auswählen."
            )
            return
        warnings = quality_warnings(self.photos)
        if warnings:
            answer = QMessageBox.question(
                self,
                "Qualitätscheck",
                f"{len(warnings)} Warnungen gefunden. Trotzdem Export öffnen?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                self.filter_combo.setCurrentText(FILTER_SELECTED)
                return
        save_project_state(
            Path("cache") / "project-state-v1.json",
            self.photos,
            self.series,
            self.manual_corrections,
        )
        dialog = ExportDialog(self.photos, self)
        dialog.exec()

    def _update_status(self) -> None:
        total = len(self.photos)
        selected = sum(photo.selected for photo in self.photos)
        ai_selected = sum(photo.ai_selected for photo in self.photos)
        favorites = sum(photo.favorite for photo in self.photos)
        reviewed, reviewable = review_progress(self.photos)
        visible = len(self._visible_photos()) if total else 0
        self.summary_label.setText(
            f"{total} Fotos · {selected} ausgewählt · {ai_selected} AI · "
            f"{favorites} Favoriten · {reviewed}/{reviewable} geprüft"
        )

        if total:
            message = f"{visible} sichtbar · Vorschaubilder geladen: {self.loaded_count}/{total}"
        else:
            message = "Noch kein Fotoordner geladen"
        self.statusBar().showMessage(message)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._relayout_gallery()

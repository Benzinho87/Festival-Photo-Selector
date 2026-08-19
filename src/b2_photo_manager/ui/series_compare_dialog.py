from pathlib import Path

from PIL import Image, ImageOps
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from b2_photo_manager.models.photo import Photo


class SeriesCompareDialog(QDialog):
    winner_selected = Signal(int, object)
    selection_changed = Signal(object)

    def __init__(
        self,
        photos: list[Photo],
        start_series_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.series = self._series_map(photos)
        self.series_ids = list(self.series)
        if not self.series_ids:
            raise ValueError("No series available")
        self.series_index = (
            self.series_ids.index(start_series_id)
            if start_series_id in self.series_ids
            else 0
        )
        self.fit_to_window = True
        self.zoom_factor = 1.0
        self.image_labels: list[QLabel] = []

        self.setWindowTitle("Serienvergleich")
        self.resize(1400, 900)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.skip_done_check = QCheckBox("Entschiedene Serien überspringen")
        self.skip_done_check.setChecked(True)

        previous_button = QPushButton("Zurück")
        previous_button.clicked.connect(self.show_previous_series)
        next_button = QPushButton("Weiter")
        next_button.clicked.connect(self.show_next_series)
        fit_button = QPushButton("Fit")
        fit_button.clicked.connect(self.set_fit)
        zoom_button = QPushButton("100 %")
        zoom_button.clicked.connect(self.set_zoom_100)

        top = QHBoxLayout()
        top.addWidget(self.title_label)
        top.addStretch()
        top.addWidget(self.skip_done_check)
        top.addWidget(previous_button)
        top.addWidget(next_button)
        top.addWidget(fit_button)
        top.addWidget(zoom_button)

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.grid_widget)

        hint = QLabel(
            "Klick oder Taste 1-4 waehlt den Seriengewinner. "
            "Mehrfachauswahl bleibt per Checkbox moeglich."
        )
        hint.setStyleSheet("color: #666;")

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.scroll, 1)
        layout.addWidget(hint)

        self._create_shortcuts()
        self._render_series()

    @property
    def current_series_id(self) -> int:
        return self.series_ids[self.series_index]

    @property
    def current_photos(self) -> list[Photo]:
        return self.series[self.current_series_id]

    def _create_shortcuts(self) -> None:
        bindings = [
            (QKeySequence("1"), lambda: self.choose_winner(0)),
            (QKeySequence("2"), lambda: self.choose_winner(1)),
            (QKeySequence("3"), lambda: self.choose_winner(2)),
            (QKeySequence("4"), lambda: self.choose_winner(3)),
            (QKeySequence("0"), self.set_fit),
            (QKeySequence(Qt.Key.Key_Right), self.show_next_series),
            (QKeySequence(Qt.Key.Key_Left), self.show_previous_series),
            (QKeySequence(Qt.Key.Key_Escape), self.close),
        ]
        self.shortcuts = []
        for sequence, callback in bindings:
            shortcut = QShortcut(sequence, self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def _series_map(self, photos: list[Photo]) -> dict[int, list[Photo]]:
        by_series: dict[int, list[Photo]] = {}
        for photo in photos:
            if photo.series_id is not None:
                by_series.setdefault(photo.series_id, []).append(photo)
        return {
            series_id: sorted(items, key=lambda photo: photo.series_rank or 9999)
            for series_id, items in sorted(by_series.items())
            if len(items) > 1
        }

    def _clear_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.image_labels = []

    def _render_series(self) -> None:
        self._clear_grid()
        photos = self.current_photos
        favorite = max(photos, key=lambda photo: photo.ai_score or 0.0)
        self.title_label.setText(
            f"Serie {self.current_series_id} · {self.series_index + 1} von {len(self.series_ids)}"
        )
        columns = 4 if len(photos) >= 4 else max(2, len(photos))
        for index, photo in enumerate(photos):
            card = self._photo_panel(index, photo, photo is favorite)
            self.grid.addWidget(card, index // columns, index % columns)

    def _photo_panel(self, index: int, photo: Photo, is_ai_favorite: bool) -> QFrame:
        frame = QFrame()
        frame.setObjectName("SeriesPhoto")
        border = "3px solid #2f80ed" if is_ai_favorite else "1px solid #999"
        if photo.selected:
            border = "3px solid #2f9e44"
        frame.setStyleSheet(f"QFrame#SeriesPhoto {{ border: {border}; border-radius: 6px; }}")
        frame.mousePressEvent = lambda event, idx=index: self.choose_winner(idx)

        image = QLabel("Vorschau nicht verfuegbar")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setMinimumSize(260, 180)
        self.image_labels.append(image)
        self._load_image(photo.path, image)

        selected_check = QCheckBox("Ausgewaehlt")
        selected_check.setChecked(photo.selected)
        selected_check.stateChanged.connect(
            lambda state, item=photo: self._toggle_photo(item, state == Qt.CheckState.Checked.value)
        )

        meta = QLabel(self._meta_text(photo, is_ai_favorite))
        meta.setWordWrap(True)

        button = QPushButton(f"{index + 1}: Als Gewinner")
        button.clicked.connect(lambda _checked=False, idx=index: self.choose_winner(idx))

        layout = QVBoxLayout(frame)
        layout.addWidget(image, 1)
        layout.addWidget(meta)
        layout.addWidget(selected_check)
        layout.addWidget(button)
        return frame

    def _meta_text(self, photo: Photo, is_ai_favorite: bool) -> str:
        warnings = []
        if photo.ai_analysis is not None:
            tech = photo.ai_analysis.technical
            if tech.sharpness < 0.45:
                warnings.append("unscharf")
            if tech.exposure < 0.35 or tech.clipping < 0.35:
                warnings.append("Belichtung kritisch")
        return (
            f"<b>{photo.path.name}</b><br>"
            f"AI {photo.ai_score or 0.0:.0%} · Rang {photo.series_rank or '-'}"
            f"{' · AI-Favorit' if is_ai_favorite else ''}<br>"
            f"{'Warnung: ' + ', '.join(warnings) if warnings else 'Keine technische Warnung'}"
        )

    def _load_image(self, path: Path, label: QLabel) -> None:
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                raw = image.tobytes("raw", "RGB")
                qimage = QImage(
                    raw, image.width, image.height, image.width * 3, QImage.Format.Format_RGB888
                ).copy()
            pixmap = QPixmap.fromImage(qimage)
            if self.fit_to_window:
                pixmap = pixmap.scaled(
                    340,
                    240,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            else:
                pixmap = pixmap.scaled(
                    int(pixmap.width() * self.zoom_factor),
                    int(pixmap.height() * self.zoom_factor),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            label.setPixmap(pixmap)
        except Exception as exc:
            label.setText(f"Bild konnte nicht geladen werden:\n{exc}")

    def _toggle_photo(self, photo: Photo, selected: bool) -> None:
        photo.selected = selected
        self.selection_changed.emit(photo)

    def choose_winner(self, index: int) -> None:
        if index >= len(self.current_photos):
            return
        self.winner_selected.emit(self.current_series_id, self.current_photos[index].path)
        self.show_next_series()

    def show_previous_series(self) -> None:
        if self.series_index > 0:
            self.series_index -= 1
            self._render_series()

    def show_next_series(self) -> None:
        index = self.series_index + 1
        if self.skip_done_check.isChecked():
            while index < len(self.series_ids) and self._is_decided(self.series[index]):
                index += 1
        if index < len(self.series_ids):
            self.series_index = index
            self._render_series()

    def _is_decided(self, photos: list[Photo]) -> bool:
        return any(photo.manual_change == "series_override" for photo in photos)

    def set_fit(self) -> None:
        self.fit_to_window = True
        self._render_series()

    def set_zoom_100(self) -> None:
        self.fit_to_window = False
        self.zoom_factor = 1.0
        self._render_series()

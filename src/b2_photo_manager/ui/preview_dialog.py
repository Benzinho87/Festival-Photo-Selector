from PIL import Image, ImageOps
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from b2_photo_manager.models.photo import Photo


class PreviewDialog(QDialog):
    selection_changed = Signal(object)

    ZOOM_LEVELS = (1.0, 2.0, 4.0)

    def __init__(
        self,
        photos: list[Photo],
        start_index: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.photos = photos
        self.index = start_index
        self.fit_to_window = True
        self.zoom_factor = 1.0
        self.original_pixmap: QPixmap | None = None

        self.setWindowTitle("B² Photo Manager – Viewer")
        self.resize(1400, 900)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.image_label)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        previous_button = QPushButton("← Zurück")
        previous_button.clicked.connect(self.show_previous)

        next_button = QPushButton("Weiter →")
        next_button.clicked.connect(self.show_next)

        fit_button = QPushButton("Fit")
        fit_button.clicked.connect(self.set_fit)

        zoom_100_button = QPushButton("100 %")
        zoom_100_button.clicked.connect(lambda: self.set_zoom(1.0))

        zoom_200_button = QPushButton("200 %")
        zoom_200_button.clicked.connect(lambda: self.set_zoom(2.0))

        self.selection_button = QPushButton()
        self.selection_button.clicked.connect(self.toggle_selection)

        controls = QHBoxLayout()
        controls.addWidget(previous_button)
        controls.addWidget(next_button)
        controls.addStretch()
        controls.addWidget(fit_button)
        controls.addWidget(zoom_100_button)
        controls.addWidget(zoom_200_button)
        controls.addStretch()
        controls.addWidget(self.selection_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area, 1)
        layout.addWidget(self.info_label)
        layout.addLayout(controls)

        self._create_shortcuts()
        self._load_current()

    @property
    def current_photo(self) -> Photo:
        return self.photos[self.index]

    def _create_shortcuts(self) -> None:
        bindings = [
            (QKeySequence(Qt.Key.Key_Right), self.show_next),
            (QKeySequence(Qt.Key.Key_Left), self.show_previous),
            (QKeySequence(Qt.Key.Key_Space), self.toggle_selection),
            (QKeySequence("F"), self.select_current),
            (QKeySequence("X"), self.reject_current),
            (QKeySequence("0"), self.set_fit),
            (QKeySequence("1"), lambda: self.set_zoom(1.0)),
            (QKeySequence("2"), lambda: self.set_zoom(2.0)),
            (QKeySequence(Qt.Key.Key_Escape), self.close),
        ]

        self.shortcuts: list[QShortcut] = []

        for sequence, callback in bindings:
            shortcut = QShortcut(sequence, self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def _load_current(self) -> None:
        photo = self.current_photo

        try:
            with Image.open(photo.path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                raw = image.tobytes("raw", "RGB")
                qimage = QImage(
                    raw,
                    image.width,
                    image.height,
                    image.width * 3,
                    QImage.Format.Format_RGB888,
                ).copy()

            self.original_pixmap = QPixmap.fromImage(qimage)
            self._render_image()
        except Exception as exc:
            self.original_pixmap = None
            self.image_label.clear()
            self.image_label.setText(
                f"Bild konnte nicht geladen werden:\n{exc}"
            )

        self._update_info()

    def _render_image(self) -> None:
        if self.original_pixmap is None:
            return

        if self.fit_to_window:
            viewport_size = self.scroll_area.viewport().size()
            target_width = max(100, viewport_size.width() - 20)
            target_height = max(100, viewport_size.height() - 20)

            pixmap = self.original_pixmap.scaled(
                target_width,
                target_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            target_width = int(
                self.original_pixmap.width() * self.zoom_factor
            )
            target_height = int(
                self.original_pixmap.height() * self.zoom_factor
            )

            pixmap = self.original_pixmap.scaled(
                target_width,
                target_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())

    def _update_info(self) -> None:
        photo = self.current_photo
        selection_state = (
            "AUSGEWÄHLT"
            if photo.selected
            else "NICHT AUSGEWÄHLT"
        )

        zoom_text = (
            "Fit"
            if self.fit_to_window
            else f"{int(self.zoom_factor * 100)} %"
        )

        self.info_label.setText(
            f"{self.index + 1} / {len(self.photos)} · "
            f"{photo.path.name} · {selection_state} · {zoom_text}\n"
            "←/→ navigieren · Leertaste umschalten · "
            "F behalten · X abwählen · 0 Fit · 1 100 % · 2 200 %"
        )

        self.selection_button.setText(
            "Auswahl aufheben"
            if photo.selected
            else "Auswählen"
        )

    def show_previous(self) -> None:
        if self.index == 0:
            return

        self.index -= 1
        self._load_current()

    def show_next(self) -> None:
        if self.index >= len(self.photos) - 1:
            return

        self.index += 1
        self._load_current()

    def toggle_selection(self) -> None:
        photo = self.current_photo
        photo.selected = not photo.selected
        self.selection_changed.emit(photo)
        self._update_info()

    def select_current(self) -> None:
        photo = self.current_photo

        if not photo.selected:
            photo.selected = True
            self.selection_changed.emit(photo)

        self._update_info()

    def reject_current(self) -> None:
        photo = self.current_photo

        if photo.selected:
            photo.selected = False
            self.selection_changed.emit(photo)

        self._update_info()

    def set_fit(self) -> None:
        self.fit_to_window = True
        self._render_image()
        self._update_info()

    def set_zoom(self, factor: float) -> None:
        self.fit_to_window = False
        self.zoom_factor = factor
        self._render_image()
        self._update_info()

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()

            if delta > 0:
                self._zoom_step(1)
            elif delta < 0:
                self._zoom_step(-1)

            event.accept()
            return

        super().wheelEvent(event)

    def _zoom_step(self, direction: int) -> None:
        current_index = 0

        if not self.fit_to_window:
            current_index = min(
                range(len(self.ZOOM_LEVELS)),
                key=lambda index: abs(
                    self.ZOOM_LEVELS[index] - self.zoom_factor
                ),
            )

        target_index = max(
            0,
            min(
                len(self.ZOOM_LEVELS) - 1,
                current_index + direction,
            ),
        )

        self.set_zoom(self.ZOOM_LEVELS[target_index])

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        if self.fit_to_window:
            self._render_image()

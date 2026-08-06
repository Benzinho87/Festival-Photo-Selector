from PIL import Image, ImageOps
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from src.models.photo import Photo


class PreviewDialog(QDialog):
    selection_changed = Signal(object)

    def __init__(self, photos: list[Photo], start_index: int, parent=None):
        super().__init__(parent)
        self.photos = photos
        self.index = start_index
        self.current_pixmap: QPixmap | None = None

        self.setWindowTitle("Großansicht")
        self.resize(1280, 850)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(800, 600)

        self.info = QLabel()
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        previous_button = QPushButton("← Zurück")
        previous_button.clicked.connect(self.show_previous)

        self.select_button = QPushButton()
        self.select_button.clicked.connect(self.toggle_selection)

        next_button = QPushButton("Weiter →")
        next_button.clicked.connect(self.show_next)

        controls = QHBoxLayout()
        controls.addWidget(previous_button)
        controls.addStretch()
        controls.addWidget(self.select_button)
        controls.addStretch()
        controls.addWidget(next_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label, 1)
        layout.addWidget(self.info)
        layout.addLayout(controls)

        self._create_shortcuts()
        self.load_current()

    def _create_shortcuts(self) -> None:
        shortcuts = [
            (QKeySequence(Qt.Key.Key_Right), self.show_next),
            (QKeySequence(Qt.Key.Key_Left), self.show_previous),
            (QKeySequence(Qt.Key.Key_Space), self.toggle_selection),
            (QKeySequence("F"), self.select_current),
            (QKeySequence("X"), self.reject_current),
            (QKeySequence(Qt.Key.Key_Escape), self.close),
        ]

        self.shortcuts = []
        for sequence, callback in shortcuts:
            shortcut = QShortcut(sequence, self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def current_photo(self) -> Photo:
        return self.photos[self.index]

    def load_current(self) -> None:
        photo = self.current_photo()

        try:
            with Image.open(photo.path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((1800, 1200), Image.Resampling.LANCZOS)
                data = image.tobytes("raw", "RGB")
                qimage = QImage(
                    data,
                    image.width,
                    image.height,
                    image.width * 3,
                    QImage.Format.Format_RGB888,
                ).copy()
                self.current_pixmap = QPixmap.fromImage(qimage)
        except Exception as exc:
            self.current_pixmap = None
            self.image_label.setText(f"Bild konnte nicht geladen werden:\n{exc}")

        self.refresh_view()

    def refresh_view(self) -> None:
        photo = self.current_photo()

        if self.current_pixmap is not None:
            scaled = self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)

        state = "Ausgewählt" if photo.selected else "Nicht ausgewählt"
        self.info.setText(
            f"{self.index + 1}/{len(self.photos)} · {photo.path.name} · {state}\n"
            "←/→ navigieren · Leertaste umschalten · F auswählen · X abwählen"
        )
        self.select_button.setText(
            "Auswahl aufheben" if photo.selected else "Auswählen"
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.refresh_view()

    def show_previous(self) -> None:
        if self.index > 0:
            self.index -= 1
            self.load_current()

    def show_next(self) -> None:
        if self.index < len(self.photos) - 1:
            self.index += 1
            self.load_current()

    def toggle_selection(self) -> None:
        photo = self.current_photo()
        photo.selected = not photo.selected
        self.selection_changed.emit(photo)
        self.refresh_view()

    def select_current(self) -> None:
        photo = self.current_photo()
        if not photo.selected:
            photo.selected = True
            self.selection_changed.emit(photo)
        self.refresh_view()

    def reject_current(self) -> None:
        photo = self.current_photo()
        if photo.selected:
            photo.selected = False
            self.selection_changed.emit(photo)
        self.refresh_view()

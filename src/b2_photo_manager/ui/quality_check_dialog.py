from pathlib import Path

from PIL import Image, ImageOps
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.review import (
    BLUR_SHARPNESS_THRESHOLD,
    EXPOSURE_WARNING_THRESHOLD,
    QualityWarning,
    grouped_quality_warnings,
    quality_warnings,
)


class QualityCheckDialog(QDialog):
    show_photo_requested = Signal(object)
    compare_series_requested = Signal(int)
    remove_from_selection_requested = Signal(object)

    def __init__(self, photos: list[Photo], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.photos = photos
        self.by_path = {photo.path: photo for photo in photos}
        self.setWindowTitle("Qualitaetscheck")
        self.resize(920, 720)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.content)

        refresh_button = QPushButton("Aktualisieren")
        refresh_button.clicked.connect(self.refresh)
        continue_button = QPushButton("Trotzdem exportieren")
        continue_button.clicked.connect(self.accept)
        close_button = QPushButton("Zurueck")
        close_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(refresh_button)
        buttons.addStretch()
        buttons.addWidget(close_button)
        buttons.addWidget(continue_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(scroll, 1)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        warnings = quality_warnings(self.photos)
        groups = grouped_quality_warnings(warnings)
        if not warnings:
            self.summary_label.setText("Keine Qualitaetswarnungen fuer die aktuelle Auswahl.")
            return
        self.summary_label.setText(
            f"{len(warnings)} Hinweise in {len(groups)} Gruppen. "
            "Sie koennen korrigieren oder trotzdem exportieren."
        )
        for group in groups:
            title = QLabel(f"<b>{len(group.warnings)} {group.title}</b><br>{group.explanation}")
            title.setWordWrap(True)
            self.content_layout.addWidget(title)
            for warning in group.warnings:
                self.content_layout.addWidget(self._warning_row(warning))
            self.content_layout.addSpacing(12)

    def _warning_row(self, warning: QualityWarning) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        paths = (warning.path, *warning.related_paths)
        names = ", ".join(path.name for path in paths)

        thumb = QLabel()
        thumb.setFixedSize(96, 72)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_thumbnail(warning.path, thumb)

        text = QLabel(f"<b>{names}</b><br>{warning.message}<br>{self._detail_text(warning)}")
        text.setWordWrap(True)

        show_button = QPushButton("Bild anzeigen")
        show_button.clicked.connect(lambda: self.show_photo_requested.emit(warning.path))
        remove_button = QPushButton("Aus Auswahl entfernen")
        remove_button.clicked.connect(lambda: self._remove_paths(paths))

        buttons = QVBoxLayout()
        buttons.addWidget(show_button)
        if warning.warning_type in {"duplicate", "series_overlap"}:
            series_id = self._series_id_for_warning(warning)
            if series_id is not None:
                compare_button = QPushButton("Serie vergleichen")
                compare_button.clicked.connect(
                    lambda _checked=False, item=series_id: self.compare_series_requested.emit(item)
                )
                buttons.addWidget(compare_button)
        buttons.addWidget(remove_button)
        buttons.addStretch()

        layout = QHBoxLayout(frame)
        layout.addWidget(thumb)
        layout.addWidget(text, 1)
        layout.addLayout(buttons)
        return frame

    def _load_thumbnail(self, path: Path, label: QLabel) -> None:
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((96, 72))
                raw = image.tobytes("raw", "RGB")
                qimage = QImage(
                    raw, image.width, image.height, image.width * 3, QImage.Format.Format_RGB888
                ).copy()
            label.setPixmap(QPixmap.fromImage(qimage))
        except Exception:
            label.setText("Keine Vorschau")

    def _detail_text(self, warning: QualityWarning) -> str:
        photo = self.by_path.get(warning.path)
        if photo is None or photo.ai_analysis is None:
            return "Grundlage: gespeicherte Auswahl- und Seriendaten."
        tech = photo.ai_analysis.technical
        if warning.warning_type == "blur":
            return f"Schaerfe {tech.sharpness:.0%}, Schwelle {BLUR_SHARPNESS_THRESHOLD:.0%}."
        if warning.warning_type == "exposure":
            return (
                f"Belichtung {tech.exposure:.0%}, Clipping {tech.clipping:.0%}, "
                f"Schwelle {EXPOSURE_WARNING_THRESHOLD:.0%}."
            )
        if warning.warning_type == "duplicate":
            return f"Gleicher Inhalts-Fingerprint: {photo.ai_analysis.perceptual_hash}."
        if warning.warning_type == "series_overlap":
            return f"Serie {photo.series_id}: mehrere Varianten sind ausgewaehlt."
        return "Hinweis aus der vorhandenen Analyse."

    def _series_id_for_warning(self, warning: QualityWarning) -> int | None:
        for path in (warning.path, *warning.related_paths):
            photo = self.by_path.get(path)
            if photo is not None and photo.series_id is not None:
                return photo.series_id
        return None

    def _remove_paths(self, paths: tuple[Path, ...]) -> None:
        for path in paths:
            self.remove_from_selection_requested.emit(path)
        self.refresh()

from PIL import Image, ImageOps
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QImage, QKeySequence, QPixmap, QShortcut, QWheelEvent
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
from b2_photo_manager.services.photo_metadata import (
    PhotoMetadata,
    format_file_size,
    read_photo_metadata,
)


class PreviewDialog(QDialog):
    selection_changed = Signal(object)
    favorite_changed = Signal(object)
    selection_decision_requested = Signal(object, bool)

    MIN_ZOOM = 0.1
    MAX_ZOOM = 8.0
    ZOOM_STEP = 1.2

    def __init__(
        self,
        photos: list[Photo],
        start_index: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not photos:
            raise ValueError("Viewer requires at least one photo")

        self.photos = photos
        self.index = min(max(start_index, 0), len(photos) - 1)
        self.fit_to_window = True
        self.zoom_factor = 1.0
        self.original_pixmap: QPixmap | None = None
        self.metadata: PhotoMetadata | None = None

        self.setWindowTitle("B² Photo Manager – Viewer")
        self.resize(1400, 900)
        self.setStyleSheet(
            "QDialog { background: #17191c; color: #f3f3f3; }"
            "QLabel { color: #f3f3f3; }"
            "QPushButton { padding: 7px 12px; }"
            "QFrame#Sidebar { background: #22252a; border-radius: 8px; }"
        )

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: #101113;")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.viewport().installEventFilter(self)

        self.position_label = QLabel()
        self.position_label.setStyleSheet("font-weight: 600;")
        self.zoom_label = QLabel()
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.metadata_label = QLabel()
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.metadata_label.setAlignment(Qt.AlignmentFlag.AlignTop)

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
        self.favorite_button = QPushButton()
        self.favorite_button.clicked.connect(self.toggle_favorite)

        top_bar = QHBoxLayout()
        top_bar.addWidget(previous_button)
        top_bar.addWidget(next_button)
        top_bar.addStretch()
        top_bar.addWidget(fit_button)
        top_bar.addWidget(zoom_100_button)
        top_bar.addWidget(zoom_200_button)
        top_bar.addWidget(self.zoom_label)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(310)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(self.position_label)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(self.metadata_label)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.favorite_button)
        sidebar_layout.addWidget(self.selection_button)

        content = QHBoxLayout()
        content.addWidget(self.scroll_area, 1)
        content.addWidget(sidebar)

        hint = QLabel(
            "←/→ navigieren · Mausrad/Trackpad zoomen · Leertaste Auswahl · "
            "F behalten · X abwählen · 0 Fit · 1 100 % · 2 200 %"
        )
        hint.setStyleSheet("color: #aeb3bb;")

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addLayout(content, 1)
        layout.addWidget(hint)

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
            self.metadata = read_photo_metadata(photo.path)
            photo.photographer = self.metadata.photographer
            with Image.open(photo.path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                raw = image.tobytes("raw", "RGB")
                qimage = QImage(
                    raw, image.width, image.height, image.width * 3, QImage.Format.Format_RGB888
                ).copy()
            self.original_pixmap = QPixmap.fromImage(qimage)
            self._render_image()
        except Exception as exc:
            self.metadata = None
            self.original_pixmap = None
            self.image_label.clear()
            self.image_label.setText(f"Bild konnte nicht geladen werden:\n{exc}")
        self._update_info()

    def _render_image(self) -> None:
        if self.original_pixmap is None:
            return
        if self.fit_to_window:
            size = self.scroll_area.viewport().size()
            pixmap = self.original_pixmap.scaled(
                max(100, size.width() - 20),
                max(100, size.height() - 20),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            pixmap = self.original_pixmap.scaled(
                int(self.original_pixmap.width() * self.zoom_factor),
                int(self.original_pixmap.height() * self.zoom_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())

    def _metadata_text(self) -> str:
        photo = self.current_photo
        ai_rows = self._ai_rows(photo)
        if self.metadata is None:
            return (
                f"<b>{photo.path.name}</b><br><br>Keine Metadaten verfügbar"
                f"{ai_rows}"
            )
        data = self.metadata
        rows = [
            ("Datei", photo.path.name),
            ("Abmessungen", f"{data.width} × {data.height} px"),
            ("Dateigröße", format_file_size(data.file_size)),
            ("Fotograf / Autor", data.photographer or "–"),
            (
                "Aufgenommen",
                data.captured_at.strftime("%d.%m.%Y %H:%M") if data.captured_at else "–",
            ),
            ("Kamera", data.camera or "–"),
            ("Objektiv", data.lens or "–"),
            ("Belichtung", data.exposure_time or "–"),
            ("Blende", data.aperture or "–"),
            ("ISO", str(data.iso) if data.iso is not None else "–"),
            ("Brennweite", data.focal_length or "–"),
        ]
        return "<br>".join(f"<b>{label}</b><br>{value}" for label, value in rows) + ai_rows

    def _ai_rows(self, photo: Photo) -> str:
        if photo.ai_analysis is None:
            return "<br><br><b>AI</b><br>Noch nicht analysiert"
        result = photo.ai_analysis
        reasons = ", ".join(result.reasons)
        return (
            "<br><br><b>AI-Empfehlung</b><br>"
            f"{photo.ai_score or 0.0:.0%} · {photo.ai_recommendation or result.recommendation}"
            f"<br><b>AI-Auswahl</b><br>{'Ja' if photo.ai_selected else 'Nein'}"
            f"<br><b>Auswahlgrund</b><br>{photo.selection_reason or '–'}"
            f"<br><b>Serie</b><br>{photo.series_id or '–'}"
            f" · Rang {photo.series_rank or '–'}"
            f"<br><b>Review</b><br>{photo.review_status}"
            f"<br><b>Manuelle Änderung</b><br>{photo.manual_change or '–'}"
            "<br><b>Teil-Scores</b><br>"
            f"Technik {result.technical.overall:.0%} · "
            f"Schärfe {result.technical.sharpness:.0%} · "
            f"Belichtung {result.technical.exposure:.0%} · "
            f"Clipping {result.technical.clipping:.0%} · "
            f"Kontrast {result.technical.contrast:.0%} · "
            f"Ästhetik {result.aesthetic.overall:.0%} · "
            f"Menschen {result.people.overall:.0%}"
            f"<br><b>Positive/negative Gründe</b><br>{reasons or '–'}"
        )

    def _update_info(self) -> None:
        photo = self.current_photo
        self.position_label.setText(f"Foto {self.index + 1} von {len(self.photos)}")
        self.metadata_label.setText(self._metadata_text())
        self.zoom_label.setText("Fit" if self.fit_to_window else f"{self.zoom_factor:.0%}")
        self.selection_button.setText(
            "✓ Auswahl aufheben" if photo.selected else "Foto auswählen"
        )
        self.favorite_button.setText(
            "★ Favorit entfernen" if photo.favorite else "☆ Als Favorit markieren"
        )

    def show_previous(self) -> None:
        if self.index > 0:
            self.index -= 1
            self._load_current()

    def show_next(self) -> None:
        if self.index < len(self.photos) - 1:
            self.index += 1
            self._load_current()

    def toggle_selection(self) -> None:
        self._set_selection(not self.current_photo.selected)
        self._update_info()

    def _set_selection(self, selected: bool) -> None:
        self.selection_decision_requested.emit(self.current_photo, selected)
        self.current_photo.selected = selected
        self.current_photo.review_status = "kept" if selected else "removed"
        self.selection_changed.emit(self.current_photo)

    def toggle_favorite(self) -> None:
        self.current_photo.favorite = not self.current_photo.favorite
        self.favorite_changed.emit(self.current_photo)
        self._update_info()

    def select_current(self) -> None:
        self._set_selection(True)
        self._update_info()

    def reject_current(self) -> None:
        self._set_selection(False)
        self._update_info()

    def set_fit(self) -> None:
        self.fit_to_window = True
        self._render_image()
        self._update_info()

    def set_zoom(self, factor: float) -> None:
        self.fit_to_window = False
        self.zoom_factor = min(max(factor, self.MIN_ZOOM), self.MAX_ZOOM)
        self._render_image()
        self._update_info()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.scroll_area.viewport() and event.type() == QEvent.Type.Wheel:
            wheel_event = event
            if isinstance(wheel_event, QWheelEvent):
                delta = wheel_event.angleDelta().y()
                if delta:
                    base = self.zoom_factor if not self.fit_to_window else 1.0
                    self.set_zoom(base * (self.ZOOM_STEP if delta > 0 else 1 / self.ZOOM_STEP))
                    wheel_event.accept()
                    return True
        return super().eventFilter(watched, event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.fit_to_window:
            self._render_image()

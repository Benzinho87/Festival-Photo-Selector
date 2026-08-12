from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from b2_photo_manager.config import CONFIG
from b2_photo_manager.models.photo import Photo


class PhotoCard(QFrame):
    selection_changed = Signal(object)
    favorite_changed = Signal(object)
    tags_requested = Signal(object)
    open_requested = Signal(object)

    def __init__(self, photo: Photo) -> None:
        super().__init__()
        self.photo = photo
        self.setObjectName("PhotoCard")
        self.setFixedWidth(CONFIG.thumbnail_width + 24)

        self.thumbnail_label = QLabel("Lade Vorschau …")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setFixedSize(CONFIG.thumbnail_width, CONFIG.thumbnail_height)

        self.selection_label = QLabel()
        self.selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ai_label = QLabel()
        self.ai_label.setWordWrap(True)

        self.favorite_button = QPushButton()
        self.favorite_button.setFixedWidth(38)
        self.favorite_button.setToolTip("Favorit umschalten")
        self.favorite_button.clicked.connect(self._toggle_favorite)

        self.tags_button = QPushButton("Tags")
        self.tags_button.clicked.connect(lambda: self.tags_requested.emit(self.photo))

        self.tags_label = QLabel()
        self.tags_label.setWordWrap(True)

        self.name_label = QLabel(photo.path.name)
        self.name_label.setWordWrap(True)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.addWidget(self.selection_label)
        meta_row.addStretch()
        meta_row.addWidget(self.favorite_button)
        meta_row.addWidget(self.tags_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.thumbnail_label)
        layout.addLayout(meta_row)
        layout.addWidget(self.ai_label)
        layout.addWidget(self.tags_label)
        layout.addWidget(self.name_label)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_style()

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        self.thumbnail_label.setPixmap(
            pixmap.scaled(
                self.thumbnail_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def set_error(self, message: str) -> None:
        self.thumbnail_label.setText(f"Fehler\\n{message}")

    def refresh_style(self) -> None:
        self.selection_label.setText("✓ Ausgewählt" if self.photo.selected else "Nicht ausgewählt")
        self.favorite_button.setText("★" if self.photo.favorite else "☆")
        if self.photo.ai_score is None:
            self.ai_label.setText("AI: noch nicht analysiert")
        else:
            selected = " · AI-Auswahl" if self.photo.ai_selected else ""
            self.ai_label.setText(
                f"AI {self.photo.ai_score:.0%} · {self.photo.ai_recommendation or 'Prüfen'}"
                f"{selected}"
            )
        if self.photo.review_status != "unreviewed" or self.photo.manual_change:
            self.ai_label.setText(
                f"{self.ai_label.text()}\nReview: {self.photo.review_status}"
                f"{' · manuell' if self.photo.manual_change else ''}"
            )
        tags_text = " · ".join(sorted(self.photo.tags)) if self.photo.tags else "Keine Tags"
        self.tags_label.setText(tags_text)

        if self.photo.selected:
            border = "3px solid #3ba55d"
        elif self.photo.ai_selected:
            border = "2px solid #4f8cff"
        else:
            border = "1px solid #777"
        self.setStyleSheet(
            f"""
            QFrame#PhotoCard {{
                border: {border};
                border-radius: 10px;
            }}
            """
        )

    def _toggle_favorite(self) -> None:
        self.photo.favorite = not self.photo.favorite
        self.refresh_style()
        self.favorite_changed.emit(self.photo)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.photo.selected = not self.photo.selected
            self.selection_changed.emit(self.photo)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.photo.path)
        super().mouseDoubleClickEvent(event)

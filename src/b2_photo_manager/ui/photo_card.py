from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from b2_photo_manager.config import CONFIG
from b2_photo_manager.models.photo import Photo


class PhotoCard(QFrame):
    selection_changed = Signal(object)
    open_requested = Signal(object)

    def __init__(self, photo: Photo) -> None:
        super().__init__()

        self.photo = photo
        self.setObjectName("PhotoCard")
        self.setFixedWidth(CONFIG.thumbnail_width + 24)

        self.thumbnail_label = QLabel("Lade Vorschau …")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setFixedSize(
            CONFIG.thumbnail_width,
            CONFIG.thumbnail_height,
        )

        self.selection_label = QLabel()
        self.selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selection_label.setMinimumWidth(92)

        self.name_label = QLabel(photo.path.name)
        self.name_label.setWordWrap(True)
        self.name_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.addWidget(self.selection_label)
        meta_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.thumbnail_label)
        layout.addLayout(meta_row)
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
        self.thumbnail_label.setText(f"Fehler\n{message}")

    def refresh_style(self) -> None:
        if self.photo.selected:
            self.selection_label.setText("✓ Ausgewählt")
            self.selection_label.setStyleSheet(
                "font-weight: 600; padding: 3px 6px;"
            )
            self.setStyleSheet(
                """
                QFrame#PhotoCard {
                    border: 3px solid #3ba55d;
                    border-radius: 10px;
                }
                """
            )
        else:
            self.selection_label.setText("Nicht ausgewählt")
            self.selection_label.setStyleSheet(
                "padding: 3px 6px;"
            )
            self.setStyleSheet(
                """
                QFrame#PhotoCard {
                    border: 1px solid #777;
                    border-radius: 10px;
                }
                """
            )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.photo.selected = not self.photo.selected
            self.selection_changed.emit(self.photo)

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.photo.path)

        super().mouseDoubleClickEvent(event)

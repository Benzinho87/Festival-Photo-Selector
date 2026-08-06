from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from src.config import CONFIG
from src.models.photo import Photo

class PhotoCard(QFrame):
    selection_changed = Signal(object)
    open_requested = Signal(Path)

    def __init__(self, photo: Photo) -> None:
        super().__init__()
        self.photo = photo
        self.setObjectName("photoCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(CONFIG.thumbnail_width + 20)
        self.image_label = QLabel("Lädt …")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(CONFIG.thumbnail_width, CONFIG.thumbnail_height)
        self.image_label.setStyleSheet("background:#242424;color:#aaa;border-radius:6px;")
        self.name_label = QLabel(photo.path.name)
        self.name_label.setWordWrap(True)
        self.name_label.setToolTip(str(photo.path))
        self.name_label.setMaximumHeight(42)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(8)
        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        self.refresh_style()

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        self.image_label.setPixmap(pixmap)

    def set_error(self, message: str) -> None:
        self.image_label.setText("Fehler")
        self.image_label.setToolTip(message)

    def refresh_style(self) -> None:
        if self.photo.selected:
            self.setStyleSheet("QFrame#photoCard{background:#213a2a;border:3px solid #41b96b;border-radius:10px;}")
        else:
            self.setStyleSheet("QFrame#photoCard{background:#1c1c1c;border:1px solid #3a3a3a;border-radius:10px;}QFrame#photoCard:hover{border:2px solid #777;}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.photo.selected = not self.photo.selected
            self.refresh_style()
            self.selection_changed.emit(self.photo)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.photo.path)
        super().mouseDoubleClickEvent(event)

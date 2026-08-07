from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from b2_photo_manager.config import CONFIG
from b2_photo_manager.models.photo import Photo

class PhotoCard(QFrame):
    selection_changed = Signal(object)
    open_requested = Signal(Path)
    def __init__(self, photo: Photo) -> None:
        super().__init__()
        self.photo=photo
        self.setObjectName("photoCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(CONFIG.thumbnail_width+20)
        self.image_label=QLabel("Lädt …")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(CONFIG.thumbnail_width, CONFIG.thumbnail_height)
        self.name_label=QLabel(photo.path.name)
        self.name_label.setWordWrap(True)
        self.name_label.setToolTip(str(photo.path))
        layout=QVBoxLayout(self)
        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        self.refresh_style()
    def set_thumbnail(self, pixmap: QPixmap) -> None:
        self.image_label.setPixmap(pixmap)
    def set_error(self, message: str) -> None:
        self.image_label.setText("Fehler")
        self.image_label.setToolTip(message)
    def refresh_style(self) -> None:
        border="3px solid #41b96b" if self.photo.selected else "1px solid #3a3a3a"
        self.setStyleSheet(f"QFrame#photoCard {{background:#1c1c1c;border:{border};border-radius:10px;}}")
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button()==Qt.MouseButton.LeftButton:
            self.photo.selected=not self.photo.selected
            self.refresh_style()
            self.selection_changed.emit(self.photo)
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button()==Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.photo.path)
        super().mouseDoubleClickEvent(event)

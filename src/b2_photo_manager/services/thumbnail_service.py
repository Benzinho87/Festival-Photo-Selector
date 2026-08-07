from pathlib import Path

from PIL import Image, ImageOps
from PySide6.QtCore import QObject, QRunnable, Signal
from PySide6.QtGui import QImage

from b2_photo_manager.config import CONFIG


class ThumbnailSignals(QObject):
    loaded = Signal(Path, QImage)
    failed = Signal(Path, str)


class ThumbnailWorker(QRunnable):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.signals = ThumbnailSignals()

    def run(self) -> None:
        try:
            with Image.open(self.path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail(
                    (
                        CONFIG.thumbnail_width,
                        CONFIG.thumbnail_height,
                    )
                )

                raw = image.tobytes("raw", "RGB")
                qimage = QImage(
                    raw,
                    image.width,
                    image.height,
                    image.width * 3,
                    QImage.Format.Format_RGB888,
                ).copy()

            self.signals.loaded.emit(self.path, qimage)
        except Exception as exc:
            self.signals.failed.emit(self.path, str(exc))

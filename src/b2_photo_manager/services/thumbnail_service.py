from pathlib import Path
from PIL import Image, ImageOps
from PySide6.QtCore import QObject, QRunnable, Signal, Slot
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

    @Slot()
    def run(self) -> None:
        try:
            with Image.open(self.path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((CONFIG.thumbnail_width, CONFIG.thumbnail_height), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (CONFIG.thumbnail_width, CONFIG.thumbnail_height), (36,36,36))
                offset=((CONFIG.thumbnail_width-image.width)//2,(CONFIG.thumbnail_height-image.height)//2)
                canvas.paste(image, offset)
                raw=canvas.tobytes("raw","RGB")
                qimage=QImage(raw, canvas.width, canvas.height, canvas.width*3, QImage.Format.Format_RGB888).copy()
            self.signals.loaded.emit(self.path, qimage)
        except Exception as exc:
            self.signals.failed.emit(self.path, str(exc))

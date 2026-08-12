from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.cache import AnalysisCache
from b2_photo_manager.services.ai.engine import SelectionEngine
from b2_photo_manager.services.ai.models import SelectionRequest, SelectionSummary


class SelectionWorkerSignals(QObject):
    progress = Signal(int, int, object)
    finished = Signal(object)
    failed = Signal(str)


class SelectionWorker(QRunnable):
    def __init__(self, photos: list[Photo], request: SelectionRequest, cache_file: Path) -> None:
        super().__init__()
        self.photos = photos
        self.request = request
        self.cache_file = cache_file
        self.signals = SelectionWorkerSignals()
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    @Slot()
    def run(self) -> None:
        try:
            engine = SelectionEngine(cache=AnalysisCache(self.cache_file))
            summary = engine.analyze_and_select(
                self.photos,
                self.request,
                progress_callback=lambda done, total, path: self.signals.progress.emit(
                    done, total, path
                ),
                cancel_callback=lambda: self.cancelled,
            )
            self.signals.finished.emit(summary)
        except Exception as exc:
            self.signals.failed.emit(str(exc))


__all__ = ["SelectionSummary", "SelectionWorker"]

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer

from b2_photo_manager.services.project.model import Project
from b2_photo_manager.services.project.recovery import RecoveryManager
from b2_photo_manager.services.project.store import ProjectStore


class AutoSaveController(QObject):
    def __init__(
        self,
        store: ProjectStore,
        recovery: RecoveryManager,
        debounce_ms: int = 1500,
        interval_ms: int = 60000,
    ) -> None:
        super().__init__()
        self.store = store
        self.recovery = recovery
        self.project: Project | None = None
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(debounce_ms)
        self.debounce_timer.timeout.connect(self.save_if_dirty)
        self.periodic_timer = QTimer(self)
        self.periodic_timer.setInterval(interval_ms)
        self.periodic_timer.timeout.connect(self.save_if_dirty)
        self.periodic_timer.start()

    def set_project(self, project: Project | None) -> None:
        self.project = project

    def mark_dirty(self) -> None:
        if self.project is None:
            return
        self.project.mark_dirty()
        self.debounce_timer.start()

    def save_if_dirty(self) -> bool:
        if self.project is None or not self.project.dirty:
            return True
        if self.project.project_file is None:
            return False
        try:
            self.store.autosave(self.project, self.autosave_path(self.project.project_file))
        except OSError:
            self.project.last_save_failed = True
            return False
        return True

    def autosave_path(self, project_file: Path) -> Path:
        return self.recovery.recovery_file_for(project_file)

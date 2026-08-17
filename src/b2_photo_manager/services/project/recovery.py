from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RecoveryChoice(str, Enum):
    RECOVER = "recover"
    SAVED = "saved"


@dataclass(frozen=True, slots=True)
class RecoveryInfo:
    project_file: Path
    autosave_file: Path | None = None
    backup_file: Path | None = None

    @property
    def has_recovery(self) -> bool:
        return self.autosave_file is not None or self.backup_file is not None


class RecoveryManager:
    def recovery_file_for(self, project_file: Path) -> Path:
        return project_file.with_suffix(f"{project_file.suffix}.autosave")

    def backup_file_for(self, project_file: Path) -> Path:
        return project_file.with_suffix(f"{project_file.suffix}.bak")

    def inspect(self, project_file: Path) -> RecoveryInfo:
        autosave = self.recovery_file_for(project_file)
        backup = self.backup_file_for(project_file)
        autosave_file = None
        if autosave.exists() and (
            not project_file.exists() or autosave.stat().st_mtime > project_file.stat().st_mtime
        ):
            autosave_file = autosave
        backup_file = backup if backup.exists() else None
        return RecoveryInfo(project_file, autosave_file, backup_file)

    def best_recovery_path(self, project_file: Path) -> Path | None:
        info = self.inspect(project_file)
        return info.autosave_file or info.backup_file

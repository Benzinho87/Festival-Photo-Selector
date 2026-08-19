from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path

from b2_photo_manager.runtime_paths import runtime_paths


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
    def __init__(self, recovery_dir: Path | None = None) -> None:
        self.recovery_dir = recovery_dir or runtime_paths().recovery_dir

    def recovery_file_for(self, project_file: Path) -> Path:
        resolved = str(project_file.expanduser().resolve())
        digest = sha256(resolved.encode("utf-8")).hexdigest()[:16]
        return self.recovery_dir / f"{project_file.stem}-{digest}.b2project.autosave"

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

    def clear_autosave(self, project_file: Path) -> None:
        try:
            self.recovery_file_for(project_file).unlink(missing_ok=True)
        except OSError:
            pass

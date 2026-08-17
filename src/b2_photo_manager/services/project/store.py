from __future__ import annotations

import json
import os
from pathlib import Path

from b2_photo_manager.services.project.model import (
    Project,
    ProjectFileError,
    project_from_json,
    project_to_json,
)


class ProjectStore:
    def save(self, project: Project, path: Path | None = None) -> None:
        target = path or project.project_file
        if target is None:
            raise ProjectFileError("project file is not set")
        target = target.with_suffix(".b2project") if target.suffix != ".b2project" else target
        target.parent.mkdir(parents=True, exist_ok=True)
        project.project_file = target
        project.snapshot.missing_photos = tuple(
            photo.path for photo in project.snapshot.photos if not photo.path.exists()
        )
        payload = json.dumps(
            project_to_json(project),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        self._atomic_write(target, payload)
        project.dirty = False
        project.last_save_failed = False

    def autosave(self, project: Project, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            project_to_json(project),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        self._atomic_write(path, payload)

    def load(self, path: Path) -> Project:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProjectFileError("could not read project") from exc
        if not isinstance(data, dict):
            raise ProjectFileError("invalid project file")
        return project_from_json(data, path)

    def validate(self, path: Path) -> None:
        self.load(path)

    def _atomic_write(self, target: Path, payload: str) -> None:
        tmp = target.with_suffix(f"{target.suffix}.tmp")
        backup = target.with_suffix(f"{target.suffix}.bak")
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        self.validate(tmp)
        if target.exists():
            os.replace(target, backup)
        os.replace(tmp, target)
        directory = os.open(str(target.parent), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

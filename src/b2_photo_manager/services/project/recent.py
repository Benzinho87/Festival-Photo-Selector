from __future__ import annotations

import json
from pathlib import Path

from b2_photo_manager.runtime_paths import runtime_paths


class RecentProjects:
    def __init__(self, path: Path | None = None, limit: int = 5) -> None:
        self.path = path or runtime_paths().recent_projects_file
        self.limit = limit

    def list(self) -> list[Path]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        paths = [Path(item) for item in raw if isinstance(item, str)]
        existing = [path for path in paths if path.exists()]
        if existing != paths:
            self._write(existing)
        return existing[: self.limit]

    def add(self, project_file: Path) -> None:
        resolved = project_file.expanduser().resolve()
        items = [path for path in self.list() if path != resolved]
        self._write([resolved, *items][: self.limit])

    def _write(self, items: list[Path]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([str(path) for path in items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

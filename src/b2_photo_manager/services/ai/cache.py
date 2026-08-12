import json
from pathlib import Path

from b2_photo_manager.services.ai.analyzer import file_signature
from b2_photo_manager.services.ai.models import AnalysisResult


class AnalysisCache:
    def __init__(self, cache_file: Path) -> None:
        self.cache_file = cache_file
        self._items: dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        if not self.cache_file.exists():
            self._items = {}
            return
        try:
            payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._items = {}
            return
        self._items = payload if isinstance(payload, dict) else {}

    def get(self, path: Path) -> AnalysisResult | None:
        key = str(path.resolve())
        payload = self._items.get(key)
        if not isinstance(payload, dict):
            return None
        try:
            result = AnalysisResult.from_json(payload)
        except (KeyError, TypeError, ValueError):
            return None
        if result.file_signature != file_signature(path):
            return None
        return result

    def set(self, result: AnalysisResult) -> None:
        self._items[str(result.path.resolve())] = result.to_json()

    def save(self) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(
            json.dumps(self._items, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )



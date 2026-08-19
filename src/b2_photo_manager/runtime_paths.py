from __future__ import annotations

import platform
from dataclasses import dataclass
from pathlib import Path

APP_DIR_NAME = "B2 Photo Manager"


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    app_support: Path
    cache: Path
    logs: Path

    @property
    def settings_dir(self) -> Path:
        return self.app_support / "settings"

    @property
    def recovery_dir(self) -> Path:
        return self.app_support / "recovery"

    @property
    def recent_projects_file(self) -> Path:
        return self.app_support / "recent-projects.json"

    @property
    def ai_cache_dir(self) -> Path:
        return self.cache / "ai"

    @property
    def thumbnail_cache_dir(self) -> Path:
        return self.cache / "thumbnails"

    @property
    def log_file(self) -> Path:
        return self.logs / "b2-photo-manager.log"

    def ensure(self) -> None:
        for path in (
            self.app_support,
            self.settings_dir,
            self.recovery_dir,
            self.cache,
            self.ai_cache_dir,
            self.thumbnail_cache_dir,
            self.logs,
        ):
            path.mkdir(parents=True, exist_ok=True)


def runtime_paths(home: Path | None = None, system: str | None = None) -> RuntimePaths:
    home_dir = home or Path.home()
    system_name = system or platform.system()
    if system_name == "Darwin":
        return RuntimePaths(
            app_support=home_dir / "Library" / "Application Support" / APP_DIR_NAME,
            cache=home_dir / "Library" / "Caches" / APP_DIR_NAME,
            logs=home_dir / "Library" / "Logs" / APP_DIR_NAME,
        )
    if system_name == "Windows":
        base = home_dir / "AppData" / "Local" / APP_DIR_NAME
        return RuntimePaths(
            app_support=base,
            cache=base / "Cache",
            logs=base / "Logs",
        )
    config_base = home_dir / ".local" / "share" / APP_DIR_NAME
    return RuntimePaths(
        app_support=config_base,
        cache=home_dir / ".cache" / APP_DIR_NAME,
        logs=home_dir / ".local" / "state" / APP_DIR_NAME / "logs",
    )

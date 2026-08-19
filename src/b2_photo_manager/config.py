from dataclasses import dataclass
from pathlib import Path

from b2_photo_manager import __version__


@dataclass(frozen=True)
class AppConfig:
    app_name: str = "B² Photo Manager"
    version: str = __version__
    thumbnail_width: int = 240
    thumbnail_height: int = 170
    thumbnail_min_columns: int = 1
    gallery_spacing: int = 14
    default_photo_directory: Path = Path.home() / "Pictures"


CONFIG = AppConfig()

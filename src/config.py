from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class AppConfig:
    app_name: str = "Festival Photo Selector"
    version: str = "0.2.0"
    default_export_count: int = 80
    default_max_edge: int = 1920
    default_jpeg_quality: int = 82
    default_filename_prefix: str = "festival"
    thumbnail_width: int = 240
    thumbnail_height: int = 170
    thumbnail_columns: int = 4
    cache_dir: Path = Path("cache")
    export_dir: Path = Path("exports")

CONFIG = AppConfig()

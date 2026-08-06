from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    app_name: str = "Festival Photo Selector"
    version: str = "0.3.0"
    thumbnail_width: int = 240
    thumbnail_height: int = 170
    thumbnail_columns: int = 4

CONFIG = AppConfig()

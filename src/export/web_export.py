from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportSettings:
    output_dir: Path
    filename_prefix: str
    max_edge: int = 1920
    jpeg_quality: int = 82


def export_images(paths: list[Path], settings: ExportSettings) -> list[Path]:
    raise NotImplementedError("Der Web-Export wird in Phase 3 ergänzt.")

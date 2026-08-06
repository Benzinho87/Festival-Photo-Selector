from dataclasses import dataclass

@dataclass(frozen=True)
class ExportPreset:
    name: str
    format: str
    max_edge: int | None
    width: int | None
    height: int | None
    crop: bool
    max_file_size_kb: int
    start_quality: int
    min_quality: int
    filename_suffix: str

PRESETS = {
    "Website": ExportPreset("Website", "JPEG", 1920, None, None, False, 450, 88, 65, ""),
    "Thumbnail": ExportPreset("Thumbnail", "JPEG", None, 600, 400, True, 100, 86, 55, "-thumb"),
    "Website groß": ExportPreset("Website groß", "JPEG", 2560, None, None, False, 800, 90, 68, "-large"),
    "WebP Website": ExportPreset("WebP Website", "WEBP", 1920, None, None, False, 300, 86, 60, ""),
}

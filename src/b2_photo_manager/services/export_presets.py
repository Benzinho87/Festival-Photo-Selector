from dataclasses import dataclass, replace
from enum import StrEnum


class ExportFormat(StrEnum):
    WEBP = "webp"
    JPG = "jpg"


class ResizeMode(StrEnum):
    LONG_EDGE = "long_edge"
    BOUNDING_BOX = "bounding_box"


@dataclass(frozen=True, slots=True)
class ExportPreset:
    key: str
    name: str
    output_format: ExportFormat
    resize_mode: ResizeMode
    long_edge: int | None
    max_width: int | None
    max_height: int | None
    quality: int
    keep_metadata: bool
    filename_prefix: str
    start_number: int
    number_padding: int
    target_size_kb: int | None = None

    def normalized(self) -> "ExportPreset":
        return replace(
            self,
            quality=min(max(self.quality, 1), 100),
            start_number=max(self.start_number, 0),
            number_padding=max(self.number_padding, 1),
            long_edge=self.long_edge if self.long_edge and self.long_edge > 0 else None,
            max_width=self.max_width if self.max_width and self.max_width > 0 else None,
            max_height=self.max_height if self.max_height and self.max_height > 0 else None,
            target_size_kb=self.target_size_kb
            if self.target_size_kb and self.target_size_kb > 0
            else None,
        )


EXPORT_PRESETS: tuple[ExportPreset, ...] = (
    ExportPreset(
        key="website",
        name="Website",
        output_format=ExportFormat.WEBP,
        resize_mode=ResizeMode.LONG_EDGE,
        long_edge=1800,
        max_width=None,
        max_height=None,
        quality=82,
        keep_metadata=False,
        filename_prefix="website",
        start_number=1,
        number_padding=3,
        target_size_kb=500,
    ),
    ExportPreset(
        key="thumbnail",
        name="Thumbnail",
        output_format=ExportFormat.WEBP,
        resize_mode=ResizeMode.LONG_EDGE,
        long_edge=600,
        max_width=None,
        max_height=None,
        quality=78,
        keep_metadata=False,
        filename_prefix="thumb",
        start_number=1,
        number_padding=3,
    ),
    ExportPreset(
        key="social",
        name="Social Media",
        output_format=ExportFormat.JPG,
        resize_mode=ResizeMode.LONG_EDGE,
        long_edge=2048,
        max_width=None,
        max_height=None,
        quality=88,
        keep_metadata=False,
        filename_prefix="social",
        start_number=1,
        number_padding=3,
    ),
    ExportPreset(
        key="reduced_original",
        name="Original verkleinert",
        output_format=ExportFormat.JPG,
        resize_mode=ResizeMode.BOUNDING_BOX,
        long_edge=None,
        max_width=3000,
        max_height=3000,
        quality=92,
        keep_metadata=True,
        filename_prefix="export",
        start_number=1,
        number_padding=3,
    ),
    ExportPreset(
        key="custom",
        name="Benutzerdefiniert",
        output_format=ExportFormat.JPG,
        resize_mode=ResizeMode.LONG_EDGE,
        long_edge=1800,
        max_width=None,
        max_height=None,
        quality=85,
        keep_metadata=False,
        filename_prefix="custom",
        start_number=1,
        number_padding=3,
    ),
)


def presets_by_name() -> dict[str, ExportPreset]:
    return {preset.name: preset for preset in EXPORT_PRESETS}

from dataclasses import dataclass, replace
from enum import StrEnum


class ExportFormat(StrEnum):
    WEBP = "webp"
    JPG = "jpg"


class ResizeMode(StrEnum):
    ORIGINAL = "original"
    LONG_EDGE = "long_edge"
    BOUNDING_BOX = "bounding_box"


class FilenameMode(StrEnum):
    PREFIX_NUMBER = "prefix_number"
    ORIGINAL_NUMBER = "original_number"


class ConflictMode(StrEnum):
    AUTO_RENAME = "auto_rename"
    SKIP = "skip"


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
    filename_mode: FilenameMode
    start_number: int
    number_padding: int
    include_photographer: bool = False
    target_size_kb: int | None = None
    conflict_mode: ConflictMode = ConflictMode.AUTO_RENAME

    def normalized(self) -> "ExportPreset":
        resize_mode = ResizeMode(self.resize_mode)
        max_width = self.max_width
        max_height = self.max_height
        if resize_mode == ResizeMode.LONG_EDGE:
            resize_mode = ResizeMode.BOUNDING_BOX
            max_width = self.long_edge
            max_height = self.long_edge

        return replace(
            self,
            resize_mode=resize_mode,
            quality=min(max(self.quality, 1), 100),
            start_number=max(self.start_number, 0),
            number_padding=max(self.number_padding, 1),
            long_edge=None,
            max_width=max_width if max_width and max_width > 0 else None,
            max_height=max_height if max_height and max_height > 0 else None,
            filename_mode=FilenameMode(self.filename_mode),
            conflict_mode=ConflictMode(self.conflict_mode),
            target_size_kb=self.target_size_kb
            if self.target_size_kb and self.target_size_kb > 0
            else None,
        )


EXPORT_PRESETS: tuple[ExportPreset, ...] = (
    ExportPreset(
        key="website",
        name="Website",
        output_format=ExportFormat.WEBP,
        resize_mode=ResizeMode.BOUNDING_BOX,
        long_edge=None,
        max_width=1800,
        max_height=1800,
        quality=82,
        keep_metadata=False,
        filename_prefix="website",
        filename_mode=FilenameMode.PREFIX_NUMBER,
        start_number=1,
        number_padding=3,
        include_photographer=False,
        target_size_kb=500,
    ),
    ExportPreset(
        key="thumbnail",
        name="E-Mail / klein",
        output_format=ExportFormat.WEBP,
        resize_mode=ResizeMode.BOUNDING_BOX,
        long_edge=None,
        max_width=1200,
        max_height=1200,
        quality=78,
        keep_metadata=False,
        filename_prefix="thumb",
        filename_mode=FilenameMode.PREFIX_NUMBER,
        start_number=1,
        number_padding=3,
        include_photographer=False,
    ),
    ExportPreset(
        key="social",
        name="Social Media",
        output_format=ExportFormat.JPG,
        resize_mode=ResizeMode.BOUNDING_BOX,
        long_edge=None,
        max_width=2048,
        max_height=2048,
        quality=88,
        keep_metadata=False,
        filename_prefix="social",
        filename_mode=FilenameMode.PREFIX_NUMBER,
        start_number=1,
        number_padding=3,
        include_photographer=False,
    ),
    ExportPreset(
        key="reduced_original",
        name="Original",
        output_format=ExportFormat.JPG,
        resize_mode=ResizeMode.ORIGINAL,
        long_edge=None,
        max_width=None,
        max_height=None,
        quality=92,
        keep_metadata=True,
        filename_prefix="export",
        filename_mode=FilenameMode.ORIGINAL_NUMBER,
        start_number=1,
        number_padding=3,
        include_photographer=False,
    ),
    ExportPreset(
        key="custom",
        name="Benutzerdefiniert",
        output_format=ExportFormat.JPG,
        resize_mode=ResizeMode.BOUNDING_BOX,
        long_edge=None,
        max_width=2560,
        max_height=2560,
        quality=85,
        keep_metadata=False,
        filename_prefix="custom",
        filename_mode=FilenameMode.PREFIX_NUMBER,
        start_number=1,
        number_padding=3,
        include_photographer=False,
    ),
)


def presets_by_name() -> dict[str, ExportPreset]:
    return {preset.name: preset for preset in EXPORT_PRESETS}

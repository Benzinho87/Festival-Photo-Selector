from collections.abc import Callable, Iterable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.export_presets import ExportFormat, ExportPreset, ResizeMode

ProgressCallback = Callable[[int, int, Path], None]


@dataclass(frozen=True, slots=True)
class ExportItemResult:
    source: Path
    destination: Path | None
    success: bool
    bytes_written: int = 0
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ExportSummary:
    destination_folder: Path
    results: tuple[ExportItemResult, ...]

    @property
    def successful_count(self) -> int:
        return sum(result.success for result in self.results)

    @property
    def error_count(self) -> int:
        return len(self.results) - self.successful_count

    @property
    def total_size(self) -> int:
        return sum(result.bytes_written for result in self.results)


def exportable_photos(photos: Iterable[Photo], favorites_only: bool = False) -> list[Photo]:
    selected = [photo for photo in photos if photo.selected]
    if favorites_only:
        return [photo for photo in selected if photo.favorite]
    return selected


def build_export_filename(
    prefix: str,
    number: int,
    padding: int,
    output_format: ExportFormat,
) -> str:
    safe_prefix = "_".join(prefix.strip().split()) or "export"
    return f"{safe_prefix}_{number:0{max(padding, 1)}d}.{output_format.value}"


def export_photos(
    photos: Iterable[Photo],
    destination_folder: Path,
    preset: ExportPreset,
    progress_callback: ProgressCallback | None = None,
) -> ExportSummary:
    normalized = preset.normalized()
    destination_folder.mkdir(parents=True, exist_ok=True)
    results: list[ExportItemResult] = []
    photo_list = list(photos)

    for index, photo in enumerate(photo_list, start=1):
        if progress_callback is not None:
            progress_callback(index - 1, len(photo_list), photo.path)
        try:
            destination = _next_available_destination(
                destination_folder,
                build_export_filename(
                    normalized.filename_prefix,
                    normalized.start_number + index - 1,
                    normalized.number_padding,
                    normalized.output_format,
                ),
            )
            bytes_written = _export_one(photo.path, destination, normalized)
            results.append(
                ExportItemResult(
                    source=photo.path,
                    destination=destination,
                    success=True,
                    bytes_written=bytes_written,
                )
            )
        except Exception as exc:
            results.append(
                ExportItemResult(
                    source=photo.path,
                    destination=None,
                    success=False,
                    error=str(exc),
                )
            )

    if progress_callback is not None:
        progress_callback(len(photo_list), len(photo_list), destination_folder)
    return ExportSummary(destination_folder=destination_folder, results=tuple(results))


def _next_available_destination(destination_folder: Path, filename: str) -> Path:
    candidate = destination_folder / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        numbered = destination_folder / f"{stem}-{counter}{suffix}"
        if not numbered.exists():
            return numbered
        counter += 1


def _export_one(source: Path, destination: Path, preset: ExportPreset) -> int:
    with Image.open(source) as image:
        exif = image.getexif() if preset.keep_metadata else None
        converted = ImageOps.exif_transpose(image).convert("RGB")
        converted.thumbnail(_target_size(converted.size, preset), Image.Resampling.LANCZOS)
        if preset.target_size_kb:
            _save_with_target_size(converted, destination, preset, exif)
        else:
            _save_image(converted, destination, preset, preset.quality, exif)
    return destination.stat().st_size


def _target_size(size: tuple[int, int], preset: ExportPreset) -> tuple[int, int]:
    width, height = size
    if preset.resize_mode == ResizeMode.BOUNDING_BOX:
        return (preset.max_width or width, preset.max_height or height)

    long_edge = preset.long_edge or max(width, height)
    if width >= height:
        return (long_edge, long_edge)
    return (long_edge, long_edge)


def _save_with_target_size(
    image: Image.Image,
    destination: Path,
    preset: ExportPreset,
    exif,
) -> None:
    target_bytes = (preset.target_size_kb or 0) * 1024
    best_payload: bytes | None = None
    best_quality = preset.quality

    for quality in range(preset.quality, 39, -6):
        payload = _encoded_image(image, preset, quality, exif)
        best_payload = payload
        best_quality = quality
        if len(payload) <= target_bytes:
            break

    if best_payload is None:
        _save_image(image, destination, preset, best_quality, exif)
        return
    destination.write_bytes(best_payload)


def _encoded_image(image: Image.Image, preset: ExportPreset, quality: int, exif) -> bytes:
    buffer = BytesIO()
    _save_image(image, buffer, preset, quality, exif)
    return buffer.getvalue()


def _save_image(image: Image.Image, destination, preset: ExportPreset, quality: int, exif) -> None:
    save_kwargs = {"quality": quality, "optimize": True}
    if preset.output_format == ExportFormat.JPG:
        save_kwargs["format"] = "JPEG"
        save_kwargs["progressive"] = True
        if exif:
            save_kwargs["exif"] = exif.tobytes()
    else:
        save_kwargs["format"] = "WEBP"
        save_kwargs["method"] = 6
        if exif:
            save_kwargs["exif"] = exif.tobytes()
    image.save(destination, **save_kwargs)

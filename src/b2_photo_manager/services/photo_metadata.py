from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import ExifTags, Image


@dataclass(frozen=True, slots=True)
class PhotoMetadata:
    width: int
    height: int
    file_size: int
    photographer: str | None = None
    camera: str | None = None
    lens: str | None = None
    captured_at: datetime | None = None
    exposure_time: str | None = None
    aperture: str | None = None
    iso: int | None = None
    focal_length: str | None = None


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip().strip("\x00")
    return text or None


def _format_fraction(value: object, suffix: str = "") -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return _clean_text(value)
    if number <= 0:
        return None
    if number < 1 and not suffix:
        denominator = round(1 / number)
        return f"1/{denominator} s"
    return f"{number:g}{suffix}"


def _parse_date(value: object) -> datetime | None:
    text = _clean_text(value)
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def read_photo_metadata(path: Path) -> PhotoMetadata:
    file_size = path.stat().st_size
    with Image.open(path) as image:
        width, height = image.size
        raw_exif = image.getexif()
        exif = {
            ExifTags.TAGS.get(tag, str(tag)): value
            for tag, value in raw_exif.items()
        }
        try:
            exif.update(
                {
                    ExifTags.TAGS.get(tag, str(tag)): value
                    for tag, value in raw_exif.get_ifd(ExifTags.IFD.Exif).items()
                }
            )
        except KeyError:
            pass

    make = _clean_text(exif.get("Make"))
    model = _clean_text(exif.get("Model"))
    camera_parts = [part for part in (make, model) if part]
    camera = " ".join(dict.fromkeys(camera_parts)) or None

    aperture_value = exif.get("FNumber")
    aperture = _format_fraction(aperture_value, "")
    if aperture:
        aperture = f"f/{aperture}"

    iso_value = exif.get("PhotographicSensitivity", exif.get("ISOSpeedRatings"))
    try:
        iso = int(iso_value) if iso_value is not None else None
    except (TypeError, ValueError):
        iso = None

    photographer = _clean_text(exif.get("Artist"))
    if not photographer:
        photographer = _clean_text(exif.get("Copyright"))

    return PhotoMetadata(
        width=width,
        height=height,
        file_size=file_size,
        photographer=photographer,
        camera=camera,
        lens=_clean_text(exif.get("LensModel")),
        captured_at=_parse_date(exif.get("DateTimeOriginal", exif.get("DateTime"))),
        exposure_time=_format_fraction(exif.get("ExposureTime")),
        aperture=aperture,
        iso=iso,
        focal_length=_format_fraction(exif.get("FocalLength"), " mm"),
    )


def format_file_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            decimals = 0 if unit == "B" else 1
            return f"{value:.{decimals}f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")

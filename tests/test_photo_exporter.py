from pathlib import Path

from PIL import Image

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.export_presets import ExportFormat, ExportPreset, ResizeMode
from b2_photo_manager.services.photo_exporter import (
    build_export_filename,
    export_photos,
    exportable_photos,
)


def _preset(**overrides) -> ExportPreset:
    values = {
        "key": "test",
        "name": "Test",
        "output_format": ExportFormat.JPG,
        "resize_mode": ResizeMode.LONG_EDGE,
        "long_edge": 100,
        "max_width": None,
        "max_height": None,
        "quality": 85,
        "keep_metadata": False,
        "filename_prefix": "event",
        "start_number": 1,
        "number_padding": 3,
        "target_size_kb": None,
    }
    values.update(overrides)
    return ExportPreset(**values)


def _image(path: Path, size: tuple[int, int] = (400, 200), exif_author: str | None = None) -> None:
    image = Image.new("RGB", size, "red")
    if exif_author:
        exif = Image.Exif()
        exif[315] = exif_author
        image.save(path, exif=exif)
    else:
        image.save(path)


def test_exportable_photos_uses_selection_and_optional_favorites() -> None:
    first = Photo(Path("first.jpg"), selected=True, favorite=False)
    second = Photo(Path("second.jpg"), selected=True, favorite=True)
    third = Photo(Path("third.jpg"), selected=False, favorite=True)

    assert exportable_photos([first, second, third]) == [first, second]
    assert exportable_photos([first, second, third], favorites_only=True) == [second]


def test_build_export_filename_uses_prefix_number_padding_and_format() -> None:
    assert build_export_filename("My Event", 7, 4, ExportFormat.WEBP) == "My_Event_0007.webp"


def test_export_resizes_and_does_not_overwrite_existing_files(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "exports"
    destination.mkdir()
    (destination / "event_001.jpg").write_text("existing")
    _image(source)

    summary = export_photos([Photo(source, selected=True)], destination, _preset())

    assert summary.successful_count == 1
    output = destination / "event_001-2.jpg"
    assert output.exists()
    with Image.open(output) as exported:
        assert exported.size == (100, 50)
    assert (destination / "event_001.jpg").read_text() == "existing"


def test_export_can_keep_or_remove_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    _image(source, exif_author="Erika")

    keep_destination = tmp_path / "keep"
    strip_destination = tmp_path / "strip"
    export_photos([Photo(source, selected=True)], keep_destination, _preset(keep_metadata=True))
    export_photos([Photo(source, selected=True)], strip_destination, _preset(keep_metadata=False))

    with Image.open(keep_destination / "event_001.jpg") as kept:
        assert kept.getexif().get(315) == "Erika"
    with Image.open(strip_destination / "event_001.jpg") as stripped:
        assert stripped.getexif().get(315) is None


def test_export_continues_after_single_file_error(tmp_path: Path) -> None:
    good = tmp_path / "good.jpg"
    bad = tmp_path / "missing.jpg"
    _image(good)

    summary = export_photos(
        [Photo(bad, selected=True), Photo(good, selected=True)],
        tmp_path / "exports",
        _preset(),
    )

    assert summary.successful_count == 1
    assert summary.error_count == 1
    assert summary.results[0].success is False
    assert summary.results[1].success is True


def test_export_target_size_reduces_large_files(tmp_path: Path) -> None:
    source = tmp_path / "large.jpg"
    _image(source, size=(1200, 900))

    summary = export_photos(
        [Photo(source, selected=True)],
        tmp_path / "exports",
        _preset(long_edge=1200, quality=95, target_size_kb=8),
    )

    assert summary.successful_count == 1
    assert summary.results[0].bytes_written <= 8 * 1024

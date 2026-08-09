from pathlib import Path

from PIL import Image

from b2_photo_manager.services.photo_metadata import format_file_size, read_photo_metadata


def test_reads_dimensions_size_and_exif_author(tmp_path: Path) -> None:
    path = tmp_path / "festival.jpg"
    image = Image.new("RGB", (120, 80), "blue")
    exif = Image.Exif()
    exif[315] = "Erika Musterfrau"
    exif[271] = "Canon"
    exif[272] = "EOS R5"
    exif[306] = "2026:08:07 21:15:00"
    image.save(path, exif=exif)

    metadata = read_photo_metadata(path)

    assert (metadata.width, metadata.height) == (120, 80)
    assert metadata.file_size == path.stat().st_size
    assert metadata.photographer == "Erika Musterfrau"
    assert metadata.camera == "Canon EOS R5"
    assert metadata.captured_at is not None
    assert metadata.captured_at.year == 2026


def test_missing_exif_is_handled(tmp_path: Path) -> None:
    path = tmp_path / "plain.png"
    Image.new("RGB", (32, 24), "white").save(path)

    metadata = read_photo_metadata(path)

    assert metadata.photographer is None
    assert metadata.camera is None
    assert metadata.captured_at is None


def test_formats_file_sizes() -> None:
    assert format_file_size(512) == "512 B"
    assert format_file_size(1536) == "1.5 KB"
    assert format_file_size(2 * 1024 * 1024) == "2.0 MB"

from pathlib import Path

import pytest

from b2_photo_manager.services.photo_finder import find_photos


def test_find_photos_recursively(tmp_path: Path) -> None:
    nested = tmp_path / "photographer-a"
    nested.mkdir()

    first = tmp_path / "a.jpg"
    second = nested / "b.WEBP"
    ignored = nested / "notes.txt"

    first.write_bytes(b"")
    second.write_bytes(b"")
    ignored.write_text("ignore", encoding="utf-8")

    assert find_photos(tmp_path) == [first, second]


def test_find_photos_rejects_missing_folder(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        find_photos(tmp_path / "missing")

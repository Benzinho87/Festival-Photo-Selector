from pathlib import Path

from src.utils.files import find_images


def test_find_images(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")

    result = find_images(tmp_path)

    assert result == [tmp_path / "a.jpg"]

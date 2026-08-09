from pathlib import Path

from b2_photo_manager.models.photo import Photo


def test_photo_defaults() -> None:
    photo = Photo(path=Path("example.jpg"))
    assert photo.selected is False
    assert photo.favorite is False
    assert photo.tags == set()
    assert photo.photographer is None


def test_photo_tags_are_independent() -> None:
    first = Photo(path=Path("a.jpg"))
    second = Photo(path=Path("b.jpg"))
    first.tags.add("Bühne")
    assert first.tags == {"Bühne"}
    assert second.tags == set()

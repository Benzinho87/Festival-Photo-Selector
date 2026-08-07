from pathlib import Path

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.photo_filter import (
    ALL_TAGS,
    FILTER_ALL,
    FILTER_FAVORITES,
    FILTER_SELECTED,
    filter_photos,
)


def make_photos() -> list[Photo]:
    return [
        Photo(Path("a.jpg"), selected=True, favorite=True, tags={"Bühne"}),
        Photo(Path("b.jpg"), tags={"Publikum"}),
        Photo(Path("c.jpg"), favorite=True, tags={"Bühne", "DJ"}),
    ]


def test_filter_all() -> None:
    photos = make_photos()
    assert filter_photos(photos, FILTER_ALL, ALL_TAGS) == photos


def test_filter_favorites_and_tag() -> None:
    result = filter_photos(make_photos(), FILTER_FAVORITES, "Bühne")
    assert [photo.path.name for photo in result] == ["a.jpg", "c.jpg"]


def test_filter_selected() -> None:
    result = filter_photos(make_photos(), FILTER_SELECTED, ALL_TAGS)
    assert [photo.path.name for photo in result] == ["a.jpg"]

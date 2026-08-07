from collections.abc import Iterable

from b2_photo_manager.models.photo import Photo

FILTER_ALL = "Alle"
FILTER_SELECTED = "Ausgewählt"
FILTER_UNSELECTED = "Nicht ausgewählt"
FILTER_FAVORITES = "Favoriten"
ALL_TAGS = "Alle Tags"


def filter_photos(
    photos: Iterable[Photo],
    state_filter: str = FILTER_ALL,
    tag_filter: str = ALL_TAGS,
) -> list[Photo]:
    result = list(photos)

    if state_filter == FILTER_SELECTED:
        result = [photo for photo in result if photo.selected]
    elif state_filter == FILTER_UNSELECTED:
        result = [photo for photo in result if not photo.selected]
    elif state_filter == FILTER_FAVORITES:
        result = [photo for photo in result if photo.favorite]

    if tag_filter and tag_filter != ALL_TAGS:
        result = [photo for photo in result if tag_filter in photo.tags]

    return result

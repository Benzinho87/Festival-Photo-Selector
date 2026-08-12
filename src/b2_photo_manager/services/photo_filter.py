from collections.abc import Iterable

from b2_photo_manager.models.photo import Photo

FILTER_ALL = "Alle"
FILTER_SELECTED = "Ausgewählt"
FILTER_UNSELECTED = "Nicht ausgewählt"
FILTER_FAVORITES = "Favoriten"
FILTER_AI_SELECTED = "AI ausgewählt"
FILTER_AI_UNSELECTED = "AI nicht ausgewählt"
FILTER_AI_SCORE_70 = "AI Score ≥ 70"
FILTER_REVIEW_UNREVIEWED = "Ungeprüft"
FILTER_REVIEW_REVIEWED = "Geprüft"
FILTER_MANUAL_CHANGED = "Manuell geändert"
FILTER_SERIES = "Serien"
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
    elif state_filter == FILTER_AI_SELECTED:
        result = [photo for photo in result if photo.ai_selected]
    elif state_filter == FILTER_AI_UNSELECTED:
        result = [photo for photo in result if not photo.ai_selected]
    elif state_filter == FILTER_AI_SCORE_70:
        result = [photo for photo in result if (photo.ai_score or 0.0) >= 0.70]
    elif state_filter == FILTER_REVIEW_UNREVIEWED:
        result = [photo for photo in result if photo.review_status == "unreviewed"]
    elif state_filter == FILTER_REVIEW_REVIEWED:
        result = [photo for photo in result if photo.review_status != "unreviewed"]
    elif state_filter == FILTER_MANUAL_CHANGED:
        result = [photo for photo in result if photo.manual_change is not None]
    elif state_filter == FILTER_SERIES:
        result = [photo for photo in result if photo.series_id is not None]

    if tag_filter and tag_filter != ALL_TAGS:
        result = [photo for photo in result if tag_filter in photo.tags]

    return result

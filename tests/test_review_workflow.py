from pathlib import Path

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.models import (
    AestheticScores,
    AnalysisResult,
    PeopleScores,
    SeriesGroup,
    TechnicalScores,
)
from b2_photo_manager.services.review import (
    CHANGE_AI_REMOVED,
    REVIEW_REMOVED,
    ReviewHistory,
    apply_series_groups,
    mark_review_decision,
    quality_warnings,
    review_photos,
    review_progress,
)


def analysis(path: Path, score: float, hash_value: str) -> AnalysisResult:
    return AnalysisResult(
        path=path,
        file_signature="1:1",
        width=100,
        height=100,
        technical=TechnicalScores(score, score, score, score, score),
        aesthetic=AestheticScores(score, score, score),
        people=PeopleScores(),
        perceptual_hash=hash_value,
        score=score,
        recommendation="",
    )


def test_review_progress_and_manual_correction() -> None:
    photo = Photo(Path("a.jpg"), selected=True, ai_selected=True)
    corrections = []
    history = ReviewHistory()

    mark_review_decision(photo, False, corrections, history)

    assert photo.selected is False
    assert photo.review_status == REVIEW_REMOVED
    assert corrections[0].change_type == CHANGE_AI_REMOVED
    assert review_progress([photo]) == (1, 1)

    changed = history.undo()
    assert changed is photo
    assert photo.selected is True


def test_review_photos_only_include_ai_selected_items() -> None:
    ai_photo = Photo(Path("ai.jpg"), selected=True, ai_selected=True)
    manual_photo = Photo(Path("manual.jpg"), selected=True, ai_selected=False)
    other_photo = Photo(Path("other.jpg"))

    assert review_photos([ai_photo, manual_photo, other_photo]) == [ai_photo]
    assert review_progress([ai_photo, manual_photo, other_photo]) == (0, 1)


def test_series_groups_assign_rank_by_ai_score() -> None:
    first = Photo(Path("a.jpg"), ai_score=0.8)
    second = Photo(Path("b.jpg"), ai_score=0.9, ai_selected=True)

    apply_series_groups([first, second], (SeriesGroup(3, (first.path, second.path)),))

    assert second.series_id == 3
    assert second.series_rank == 1
    assert second.selection_reason == "series_rank"


def test_quality_warnings_detect_blur_duplicates_and_series_overlap() -> None:
    first = Photo(Path("a.jpg"), selected=True, series_id=1)
    first.ai_analysis = analysis(first.path, 0.2, "same")
    second = Photo(Path("b.jpg"), selected=True, series_id=1)
    second.ai_analysis = analysis(second.path, 0.9, "same")

    warning_types = {warning.warning_type for warning in quality_warnings([first, second])}

    assert {"blur", "exposure", "duplicate", "series_overlap"} <= warning_types

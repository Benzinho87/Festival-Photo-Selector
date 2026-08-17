from pathlib import Path

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.engine import SelectionEngine
from b2_photo_manager.services.ai.models import (
    AestheticScores,
    AnalysisResult,
    ContentFingerprint,
    PeopleScores,
    SelectionProfile,
    SelectionRequest,
    SelectionTarget,
    TechnicalScores,
)


def attach(
    photo: Photo,
    score: float,
    hash_value: str,
    content: ContentFingerprint | None = None,
) -> Photo:
    photo.ai_analysis = AnalysisResult(
        path=photo.path,
        file_signature="1:1",
        width=100,
        height=100,
        technical=TechnicalScores(score, score, score, score, score),
        aesthetic=AestheticScores(score, score, score),
        people=PeopleScores(),
        perceptual_hash=hash_value,
        score=score,
        recommendation="",
        content=content or ContentFingerprint.empty(),
    )
    return photo


def test_selection_prefers_diversity_across_series() -> None:
    photos = [
        attach(Photo(Path("series-a-1.jpg")), 0.95, "0000000000000000"),
        attach(Photo(Path("series-a-2.jpg")), 0.94, "0000000000000001"),
        attach(Photo(Path("series-b-1.jpg")), 0.80, "ffffffffffffffff"),
    ]
    summary = SelectionEngine().select(
        photos,
        SelectionRequest(
            profile=SelectionProfile.EVENT,
            target=SelectionTarget(count=2),
        ),
    )
    assert summary.selected == (Path("series-a-1.jpg"), Path("series-b-1.jpg"))


def test_favorites_are_preserved_as_ai_selected() -> None:
    favorite = attach(Photo(Path("fav.jpg"), favorite=True), 0.2, "aaaaaaaaaaaaaaaa")
    strong = attach(Photo(Path("strong.jpg")), 0.9, "bbbbbbbbbbbbbbbb")
    SelectionEngine().select(
        [favorite, strong],
        SelectionRequest(target=SelectionTarget(count=1)),
    )
    assert favorite.ai_selected is True
    assert favorite.selected is False


def test_content_similar_photos_do_not_dominate_selection() -> None:
    same_content = ContentFingerprint(
        brightness=(0.5, 0.5, 0.5, 0.5),
        colors=(0.4, 0.35, 0.25),
        edges=(0.2, 0.2, 0.2, 0.2),
        warmth=0.6,
        aspect_ratio=0.6,
    )
    different_content = ContentFingerprint(
        brightness=(0.1, 0.8, 0.2, 0.7),
        colors=(0.2, 0.5, 0.3),
        edges=(0.8, 0.1, 0.7, 0.2),
        warmth=0.2,
        aspect_ratio=0.3,
    )
    photos = [
        attach(Photo(Path("near-a.jpg")), 0.99, "0000000000000000", same_content),
        attach(Photo(Path("near-b.jpg")), 0.98, "ffffffffffffffff", same_content),
        attach(Photo(Path("different.jpg")), 0.62, "0f0f0f0f0f0f0f0f", different_content),
    ]

    summary = SelectionEngine().select(
        photos,
        SelectionRequest(target=SelectionTarget(count=2)),
    )

    assert summary.selected == (Path("near-a.jpg"), Path("different.jpg"))

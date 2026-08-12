from pathlib import Path

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.engine import SelectionEngine
from b2_photo_manager.services.ai.models import (
    AestheticScores,
    AnalysisResult,
    PeopleScores,
    SelectionProfile,
    SelectionRequest,
    SelectionTarget,
    TechnicalScores,
)


def attach(photo: Photo, score: float, hash_value: str) -> Photo:
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

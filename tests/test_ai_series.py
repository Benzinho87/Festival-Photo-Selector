from pathlib import Path

from b2_photo_manager.services.ai.models import (
    AestheticScores,
    AnalysisResult,
    PeopleScores,
    TechnicalScores,
)
from b2_photo_manager.services.ai.series import group_similar_series


def result(name: str, hash_value: str) -> AnalysisResult:
    return AnalysisResult(
        path=Path(name),
        file_signature="1:1",
        width=100,
        height=100,
        technical=TechnicalScores(0.5, 0.5, 0.5, 0.5, 0.5),
        aesthetic=AestheticScores(0.5, 0.5, 0.5),
        people=PeopleScores(),
        perceptual_hash=hash_value,
        score=0.5,
        recommendation="Prüfen",
    )


def test_similar_hashes_are_grouped() -> None:
    groups = group_similar_series(
        [
            result("a.jpg", "0000000000000000"),
            result("b.jpg", "0000000000000001"),
            result("c.jpg", "ffffffffffffffff"),
        ],
        distance_threshold=2,
    )
    assert len(groups) == 2
    assert groups[0].photos == (Path("a.jpg"), Path("b.jpg"))

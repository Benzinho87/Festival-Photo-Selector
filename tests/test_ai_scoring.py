from pathlib import Path

import pytest

from b2_photo_manager.services.ai.models import (
    AestheticScores,
    AnalysisResult,
    PeopleScores,
    SelectionProfile,
    TechnicalScores,
)
from b2_photo_manager.services.ai.scoring import score_result


def make_result() -> AnalysisResult:
    return AnalysisResult(
        path=Path("a.jpg"),
        file_signature="1:1",
        width=100,
        height=100,
        technical=TechnicalScores(0.9, 0.8, 0.8, 0.7, 0.7),
        aesthetic=AestheticScores(0.5, 0.5, 0.5),
        people=PeopleScores(faces_present=True, face_count=2, face_sharpness=0.9),
        perceptual_hash="0f0f0f0f0f0f0f0f",
        score=0.0,
        recommendation="",
    )


def test_technical_profile_weights_technical_quality_more_strongly() -> None:
    result = make_result()
    assert score_result(result, SelectionProfile.TECHNICAL) > score_result(
        result, SelectionProfile.BALANCED
    )


def test_custom_weights_are_normalized() -> None:
    result = make_result()
    score = score_result(result, SelectionProfile.CUSTOM, {"technical": 10.0})
    assert score == pytest.approx(result.technical.overall)

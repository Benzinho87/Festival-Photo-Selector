from pathlib import Path

from b2_photo_manager.services.ai.cache import AnalysisCache
from b2_photo_manager.services.ai.models import (
    AestheticScores,
    AnalysisResult,
    PeopleScores,
    TechnicalScores,
)


def make_result(path: Path) -> AnalysisResult:
    stat = path.stat()
    return AnalysisResult(
        path=path,
        file_signature=f"{stat.st_size}:{stat.st_mtime_ns}",
        width=10,
        height=10,
        technical=TechnicalScores(0.5, 0.5, 0.5, 0.5, 0.5),
        aesthetic=AestheticScores(0.5, 0.5, 0.5),
        people=PeopleScores(),
        perceptual_hash="0000000000000000",
        score=0.5,
        recommendation="Prüfen",
    )


def test_cache_returns_matching_signature(tmp_path: Path) -> None:
    image = tmp_path / "a.jpg"
    image.write_bytes(b"photo")
    cache = AnalysisCache(tmp_path / "cache.json")
    cache.set(make_result(image))
    cache.save()

    reloaded = AnalysisCache(tmp_path / "cache.json")
    assert reloaded.get(image) is not None


def test_cache_ignores_changed_files(tmp_path: Path) -> None:
    image = tmp_path / "a.jpg"
    image.write_bytes(b"photo")
    cache = AnalysisCache(tmp_path / "cache.json")
    cache.set(make_result(image))
    cache.save()
    image.write_bytes(b"changed")

    assert AnalysisCache(tmp_path / "cache.json").get(image) is None

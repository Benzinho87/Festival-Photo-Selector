import time
from pathlib import Path

from PIL import Image

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.analyzer import PillowTechnicalAnalyzer
from b2_photo_manager.services.ai.engine import SelectionEngine
from b2_photo_manager.services.ai.models import SelectionRequest, SelectionTarget


def test_analysis_and_selection_smoke_performance(tmp_path: Path) -> None:
    paths: list[Path] = []
    for index in range(12):
        path = tmp_path / f"{index:03d}.jpg"
        Image.new("RGB", (160, 120), (index * 17, 120, 180)).save(path)
        paths.append(path)

    photos = [Photo(path) for path in paths]
    start = time.perf_counter()
    summary = SelectionEngine(analyzer=PillowTechnicalAnalyzer()).analyze_and_select(
        photos,
        SelectionRequest(target=SelectionTarget(count=5)),
    )
    elapsed = time.perf_counter() - start

    assert len(summary.selected) == 5
    assert elapsed < 5.0

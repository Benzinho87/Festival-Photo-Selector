from dataclasses import dataclass
from pathlib import Path


@dataclass
class QualityResult:
    path: Path
    sharpness: float
    brightness: float
    contrast: float
    score: float


def analyse_quality(path: Path) -> QualityResult:
    raise NotImplementedError("Die Qualitätsanalyse wird in einer späteren Phase ergänzt.")

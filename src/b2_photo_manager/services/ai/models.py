from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SelectionProfile(str, Enum):
    BALANCED = "Ausgewogen"
    TECHNICAL = "Technische Qualität"
    PEOPLE = "Menschen/Emotionen"
    EVENT = "Event/Reportage"
    BEST_PER_SERIES = "Beste Aufnahme je Serie"
    CUSTOM = "Benutzerdefiniert"


@dataclass(frozen=True, slots=True)
class SelectionTarget:
    count: int | None = None
    percent: float | None = None

    def resolve(self, total: int) -> int:
        if total <= 0:
            return 0
        if self.count is not None:
            return min(max(self.count, 0), total)
        if self.percent is not None:
            return min(max(round(total * self.percent), 0), total)
        return min(80, total)


@dataclass(frozen=True, slots=True)
class TechnicalScores:
    sharpness: float
    exposure: float
    clipping: float
    contrast: float
    noise: float

    @property
    def overall(self) -> float:
        return (
            self.sharpness * 0.34
            + self.exposure * 0.24
            + self.clipping * 0.18
            + self.contrast * 0.16
            + self.noise * 0.08
        )


@dataclass(frozen=True, slots=True)
class AestheticScores:
    composition: float
    subject_clarity: float
    visual_quality: float

    @property
    def overall(self) -> float:
        return self.composition * 0.35 + self.subject_clarity * 0.35 + self.visual_quality * 0.30


@dataclass(frozen=True, slots=True)
class PeopleScores:
    faces_present: bool = False
    face_count: int = 0
    eyes_open: float | None = None
    face_sharpness: float | None = None

    @property
    def overall(self) -> float:
        base = 0.58 if self.faces_present else 0.42
        if self.face_sharpness is not None:
            base = base * 0.7 + self.face_sharpness * 0.3
        if self.eyes_open is not None:
            base = base * 0.75 + self.eyes_open * 0.25
        return _clamp(base)


@dataclass(frozen=True, slots=True)
class ContentFingerprint:
    brightness: tuple[float, ...]
    colors: tuple[float, ...]
    edges: tuple[float, ...]
    warmth: float
    aspect_ratio: float

    @classmethod
    def empty(cls) -> "ContentFingerprint":
        return cls(
            brightness=(0.0, 0.0, 0.0, 0.0),
            colors=(0.0, 0.0, 0.0),
            edges=(0.0, 0.0, 0.0, 0.0),
            warmth=0.0,
            aspect_ratio=1.0,
        )

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    path: Path
    file_signature: str
    width: int
    height: int
    technical: TechnicalScores
    aesthetic: AestheticScores
    people: PeopleScores
    perceptual_hash: str
    score: float
    recommendation: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None
    content: ContentFingerprint = field(default_factory=ContentFingerprint.empty)

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["path"] = str(self.path)
        return data

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "AnalysisResult":
        content_data = data.get("content")
        if isinstance(content_data, dict):
            content = ContentFingerprint(
                brightness=tuple(content_data.get("brightness", (0.0, 0.0, 0.0, 0.0))),
                colors=tuple(content_data.get("colors", (0.0, 0.0, 0.0))),
                edges=tuple(content_data.get("edges", (0.0, 0.0, 0.0, 0.0))),
                warmth=float(content_data.get("warmth", 0.0)),
                aspect_ratio=float(content_data.get("aspect_ratio", 1.0)),
            )
        else:
            content = ContentFingerprint.empty()
        return cls(
            path=Path(data["path"]),
            file_signature=data["file_signature"],
            width=int(data["width"]),
            height=int(data["height"]),
            technical=TechnicalScores(**data["technical"]),
            aesthetic=AestheticScores(**data["aesthetic"]),
            people=PeopleScores(**data["people"]),
            perceptual_hash=str(data["perceptual_hash"]),
            score=float(data["score"]),
            recommendation=str(data["recommendation"]),
            reasons=tuple(data.get("reasons", ())),
            error=data.get("error"),
            content=content,
        )


@dataclass(frozen=True, slots=True)
class SeriesGroup:
    id: int
    photos: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class SelectionRequest:
    profile: SelectionProfile = SelectionProfile.BALANCED
    target: SelectionTarget = field(default_factory=SelectionTarget)
    custom_weights: dict[str, float] | None = None
    preserve_favorites: bool = True


@dataclass(frozen=True, slots=True)
class SelectionSummary:
    selected: tuple[Path, ...]
    series: tuple[SeriesGroup, ...]
    target_count: int
    errors: tuple[tuple[Path, str], ...] = ()


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

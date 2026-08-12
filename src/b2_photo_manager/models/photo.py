from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from b2_photo_manager.services.ai.models import AnalysisResult


@dataclass(slots=True)
class Photo:
    path: Path
    selected: bool = False
    ai_selected: bool = False
    ai_score: float | None = None
    ai_recommendation: str | None = None
    ai_analysis: "AnalysisResult | None" = None
    review_status: str = "unreviewed"
    review_note: str | None = None
    series_id: int | None = None
    series_rank: int | None = None
    selection_reason: str | None = None
    manual_change: str | None = None
    favorite: bool = False
    tags: set[str] = field(default_factory=set)
    rating: int = 0
    photographer: str | None = None

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.models import AnalysisResult, SeriesGroup

REVIEW_UNREVIEWED = "unreviewed"
REVIEW_KEPT = "kept"
REVIEW_REMOVED = "removed"

CHANGE_AI_REMOVED = "ai_removed"
CHANGE_MANUAL_ADDED = "manual_added"
CHANGE_SERIES_OVERRIDE = "series_override"


@dataclass(frozen=True, slots=True)
class ManualCorrection:
    path: Path
    change_type: str
    previous_selected: bool
    new_selected: bool
    series_id: int | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["path"] = str(self.path)
        return data

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ManualCorrection:
        return cls(
            path=Path(data["path"]),
            change_type=str(data["change_type"]),
            previous_selected=bool(data["previous_selected"]),
            new_selected=bool(data["new_selected"]),
            series_id=data.get("series_id"),
            timestamp=str(data["timestamp"]),
        )


@dataclass(frozen=True, slots=True)
class QualityWarning:
    path: Path
    warning_type: str
    message: str
    related_paths: tuple[Path, ...] = ()


class ReviewHistory:
    def __init__(self) -> None:
        self.undo_stack: list[tuple[Photo, dict[str, Any], dict[str, Any]]] = []
        self.redo_stack: list[tuple[Photo, dict[str, Any], dict[str, Any]]] = []

    def apply(self, photo: Photo, **changes: Any) -> None:
        before = _photo_state(photo)
        for key, value in changes.items():
            setattr(photo, key, value)
        after = _photo_state(photo)
        if before != after:
            self.undo_stack.append((photo, before, after))
            self.redo_stack.clear()

    def undo(self) -> Photo | None:
        if not self.undo_stack:
            return None
        photo, before, after = self.undo_stack.pop()
        _restore_photo_state(photo, before)
        self.redo_stack.append((photo, before, after))
        return photo

    def redo(self) -> Photo | None:
        if not self.redo_stack:
            return None
        photo, before, after = self.redo_stack.pop()
        _restore_photo_state(photo, after)
        self.undo_stack.append((photo, before, after))
        return photo


def review_progress(photos: list[Photo]) -> tuple[int, int]:
    reviewable = review_photos(photos)
    reviewed = [photo for photo in reviewable if photo.review_status != REVIEW_UNREVIEWED]
    return len(reviewed), len(reviewable)


def review_photos(photos: list[Photo]) -> list[Photo]:
    return [photo for photo in photos if photo.ai_selected]


def mark_review_decision(
    photo: Photo,
    keep: bool,
    corrections: list[ManualCorrection],
    history: ReviewHistory | None = None,
) -> None:
    previous = photo.selected
    change_type = _change_type(photo, keep)
    changes = {
        "selected": keep,
        "review_status": REVIEW_KEPT if keep else REVIEW_REMOVED,
        "manual_change": change_type,
    }
    if history is None:
        for key, value in changes.items():
            setattr(photo, key, value)
    else:
        history.apply(photo, **changes)
    if change_type is not None:
        corrections.append(
            ManualCorrection(
                path=photo.path,
                change_type=change_type,
                previous_selected=previous,
                new_selected=keep,
                series_id=photo.series_id,
            )
        )


def apply_series_groups(photos: list[Photo], groups: tuple[SeriesGroup, ...]) -> None:
    by_path = {photo.path: photo for photo in photos}
    for group in groups:
        ranked = sorted(
            (by_path[path] for path in group.photos if path in by_path),
            key=lambda photo: photo.ai_score or 0.0,
            reverse=True,
        )
        for rank, photo in enumerate(ranked, start=1):
            photo.series_id = group.id
            photo.series_rank = rank
            if photo.ai_selected and photo.selection_reason is None:
                photo.selection_reason = "series_rank" if rank == 1 else "diversity"


def choose_series_best(
    photos: list[Photo],
    series_id: int,
    best_path: Path,
    corrections: list[ManualCorrection],
    history: ReviewHistory | None = None,
) -> None:
    for photo in photos:
        if photo.series_id != series_id:
            continue
        keep = photo.path == best_path
        previous = photo.selected
        changes = {
            "selected": keep,
            "review_status": REVIEW_KEPT if keep else REVIEW_REMOVED,
            "manual_change": CHANGE_SERIES_OVERRIDE if previous != keep else photo.manual_change,
        }
        if history is None:
            for key, value in changes.items():
                setattr(photo, key, value)
        else:
            history.apply(photo, **changes)
        if previous != keep:
            corrections.append(
                ManualCorrection(photo.path, CHANGE_SERIES_OVERRIDE, previous, keep, series_id)
            )


def quality_warnings(photos: list[Photo]) -> list[QualityWarning]:
    selected = [photo for photo in photos if photo.selected]
    warnings: list[QualityWarning] = []
    by_series: dict[int, list[Photo]] = {}
    seen_hashes: dict[str, Photo] = {}
    for photo in selected:
        result = photo.ai_analysis
        if result is None:
            continue
        if result.technical.sharpness < 0.45:
            warnings.append(QualityWarning(photo.path, "blur", "Ausgewähltes Bild wirkt unscharf."))
        if result.technical.exposure < 0.35 or result.technical.clipping < 0.35:
            warnings.append(
                QualityWarning(photo.path, "exposure", "Ausgewähltes Bild ist sehr dunkel/hell.")
            )
        if result.perceptual_hash in seen_hashes:
            warnings.append(
                QualityWarning(
                    photo.path,
                    "duplicate",
                    "Auswahl enthält ein sehr ähnliches Duplikat.",
                    (seen_hashes[result.perceptual_hash].path,),
                )
            )
        else:
            seen_hashes[result.perceptual_hash] = photo
        if photo.series_id is not None:
            by_series.setdefault(photo.series_id, []).append(photo)
    for series_photos in by_series.values():
        if len(series_photos) > 1:
            first, *rest = series_photos
            warnings.append(
                QualityWarning(
                    first.path,
                    "series_overlap",
                    "Mehrere fast identische Bilder derselben Serie sind ausgewählt.",
                    tuple(photo.path for photo in rest),
                )
            )
    return warnings


def save_project_state(
    path: Path,
    photos: list[Photo],
    series: tuple[SeriesGroup, ...],
    corrections: list[ManualCorrection],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "photos": [_photo_to_json(photo) for photo in photos],
        "series": [
            {"id": group.id, "photos": [str(item) for item in group.photos]}
            for group in series
        ],
        "manual_corrections": [correction.to_json() for correction in corrections],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project_state(
    path: Path,
    photos: list[Photo],
) -> tuple[tuple[SeriesGroup, ...], list[ManualCorrection]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_path = {str(photo.path): photo for photo in photos}
    for item in payload.get("photos", []):
        photo = by_path.get(item["path"])
        if photo is None:
            continue
        _restore_saved_photo(photo, item)
    series = tuple(
        SeriesGroup(id=int(item["id"]), photos=tuple(Path(path) for path in item["photos"]))
        for item in payload.get("series", [])
    )
    corrections = [
        ManualCorrection.from_json(item) for item in payload.get("manual_corrections", [])
    ]
    return series, corrections


def _change_type(photo: Photo, keep: bool) -> str | None:
    if photo.ai_selected and not keep:
        return CHANGE_AI_REMOVED
    if not photo.ai_selected and keep:
        return CHANGE_MANUAL_ADDED
    return photo.manual_change


def _photo_state(photo: Photo) -> dict[str, Any]:
    return {
        "selected": photo.selected,
        "favorite": photo.favorite,
        "review_status": photo.review_status,
        "manual_change": photo.manual_change,
    }


def _restore_photo_state(photo: Photo, state: dict[str, Any]) -> None:
    for key, value in state.items():
        setattr(photo, key, value)


def _photo_to_json(photo: Photo) -> dict[str, Any]:
    return {
        "path": str(photo.path),
        "selected": photo.selected,
        "favorite": photo.favorite,
        "tags": sorted(photo.tags),
        "rating": photo.rating,
        "ai_selected": photo.ai_selected,
        "ai_score": photo.ai_score,
        "ai_recommendation": photo.ai_recommendation,
        "ai_analysis": photo.ai_analysis.to_json() if photo.ai_analysis is not None else None,
        "review_status": photo.review_status,
        "review_note": photo.review_note,
        "series_id": photo.series_id,
        "series_rank": photo.series_rank,
        "selection_reason": photo.selection_reason,
        "manual_change": photo.manual_change,
    }


def _restore_saved_photo(photo: Photo, data: dict[str, Any]) -> None:
    photo.selected = bool(data.get("selected", False))
    photo.favorite = bool(data.get("favorite", False))
    photo.tags = set(data.get("tags", []))
    photo.rating = int(data.get("rating", 0))
    photo.ai_selected = bool(data.get("ai_selected", False))
    photo.ai_score = data.get("ai_score")
    photo.ai_recommendation = data.get("ai_recommendation")
    photo.ai_analysis = (
        AnalysisResult.from_json(data["ai_analysis"]) if data.get("ai_analysis") else None
    )
    photo.review_status = str(data.get("review_status", REVIEW_UNREVIEWED))
    photo.review_note = data.get("review_note")
    photo.series_id = data.get("series_id")
    photo.series_rank = data.get("series_rank")
    photo.selection_reason = data.get("selection_reason")
    photo.manual_change = data.get("manual_change")

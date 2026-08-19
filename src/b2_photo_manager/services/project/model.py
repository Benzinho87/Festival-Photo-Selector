from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.models import AnalysisResult, SeriesGroup
from b2_photo_manager.services.review import REVIEW_UNREVIEWED, ManualCorrection

PROJECT_FORMAT_VERSION = 1


class ProjectFileError(ValueError):
    pass


@dataclass(slots=True)
class ProjectSnapshot:
    photos: list[Photo]
    series: tuple[SeriesGroup, ...] = ()
    manual_corrections: list[ManualCorrection] = field(default_factory=list)
    export_info: dict[str, Any] = field(default_factory=dict)
    missing_photos: tuple[Path, ...] = ()


@dataclass(slots=True)
class Project:
    name: str
    source_folder: Path
    project_file: Path | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    snapshot: ProjectSnapshot = field(default_factory=lambda: ProjectSnapshot(photos=[]))
    dirty: bool = False
    last_save_failed: bool = False

    @classmethod
    def new(cls, source_folder: Path, photos: list[Photo]) -> Project:
        return cls(
            name=source_folder.name or "Neues Projekt",
            source_folder=source_folder,
            snapshot=ProjectSnapshot(photos=photos),
            dirty=True,
        )

    def mark_dirty(self) -> None:
        self.modified_at = datetime.now(UTC)
        self.dirty = True


def project_to_json(project: Project) -> dict[str, Any]:
    return {
        "project_format_version": PROJECT_FORMAT_VERSION,
        "name": project.name,
        "source_folder": str(project.source_folder),
        "project_file": str(project.project_file) if project.project_file else None,
        "created_at": _datetime_to_json(project.created_at),
        "modified_at": _datetime_to_json(project.modified_at),
        "photos": [_photo_to_json(photo) for photo in project.snapshot.photos],
        "series": [
            {"id": group.id, "photos": [str(path) for path in group.photos]}
            for group in project.snapshot.series
        ],
        "manual_corrections": [
            correction.to_json() for correction in project.snapshot.manual_corrections
        ],
        "export_info": project.snapshot.export_info,
    }


def project_from_json(data: dict[str, Any], project_file: Path | None = None) -> Project:
    version = data.get("project_format_version")
    if not isinstance(version, int):
        raise ProjectFileError("missing project format version")
    if version > PROJECT_FORMAT_VERSION:
        raise ProjectFileError("project format is newer than this app supports")
    if version < PROJECT_FORMAT_VERSION:
        raise ProjectFileError("unsupported older project format")
    try:
        photos = [_photo_from_json(item) for item in data.get("photos", [])]
        missing = tuple(photo.path for photo in photos if not photo.path.exists())
        series = tuple(
            SeriesGroup(id=int(item["id"]), photos=tuple(Path(path) for path in item["photos"]))
            for item in data.get("series", [])
        )
        corrections = [
            ManualCorrection.from_json(item) for item in data.get("manual_corrections", [])
        ]
        project = Project(
            name=str(data["name"]),
            source_folder=Path(data["source_folder"]),
            project_file=project_file or _optional_path(data.get("project_file")),
            created_at=_datetime_from_json(data["created_at"]),
            modified_at=_datetime_from_json(data["modified_at"]),
            snapshot=ProjectSnapshot(
                photos=photos,
                series=series,
                manual_corrections=corrections,
                export_info=dict(data.get("export_info", {})),
                missing_photos=missing,
            ),
            dirty=False,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProjectFileError("invalid project file") from exc
    return project


def apply_project_snapshot(project: Project, photos: list[Photo]) -> ProjectSnapshot:
    saved_by_path = {photo.path: photo for photo in project.snapshot.photos}
    restored: list[Photo] = []
    missing: list[Path] = []
    for saved in saved_by_path.values():
        if not saved.path.exists():
            missing.append(saved.path)
        restored.append(saved)
    for photo in photos:
        if photo.path not in saved_by_path:
            restored.append(photo)
    project.snapshot.photos = restored
    project.snapshot.missing_photos = tuple(missing)
    return project.snapshot


def _photo_to_json(photo: Photo) -> dict[str, Any]:
    return {
        "path": str(photo.path),
        "selected": photo.selected,
        "favorite": photo.favorite,
        "tags": sorted(photo.tags),
        "rating": photo.rating,
        "photographer": photo.photographer,
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


def _photo_from_json(data: dict[str, Any]) -> Photo:
    photo = Photo(path=Path(data["path"]))
    photo.selected = bool(data.get("selected", False))
    photo.favorite = bool(data.get("favorite", False))
    photo.tags = set(data.get("tags", []))
    photo.rating = int(data.get("rating", 0))
    photo.photographer = data.get("photographer")
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
    return photo


def _datetime_to_json(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _datetime_from_json(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.models import (
    AestheticScores,
    AnalysisResult,
    PeopleScores,
    SeriesGroup,
    TechnicalScores,
)
from b2_photo_manager.services.project import (
    PROJECT_FORMAT_VERSION,
    AutoSaveController,
    Project,
    ProjectFileError,
    ProjectStore,
    RecentProjects,
    RecoveryManager,
)
from b2_photo_manager.services.project.model import project_to_json
from b2_photo_manager.services.review import ManualCorrection


def analysis(path: Path) -> AnalysisResult:
    return AnalysisResult(
        path=path,
        file_signature="1:1",
        width=100,
        height=80,
        technical=TechnicalScores(0.9, 0.8, 0.7, 0.6, 0.5),
        aesthetic=AestheticScores(0.5, 0.6, 0.7),
        people=PeopleScores(faces_present=True, face_count=1, face_sharpness=0.8),
        perceptual_hash="0000000000000000",
        score=0.86,
        recommendation="Empfohlen",
    )


def make_project(tmp_path: Path) -> Project:
    image = tmp_path / "a.jpg"
    image.write_bytes(b"image")
    photo = Photo(image, selected=True, favorite=True, tags={"Bühne"}, rating=4)
    photo.ai_selected = True
    photo.ai_score = 0.86
    photo.ai_recommendation = "Empfohlen"
    photo.ai_analysis = analysis(image)
    photo.review_status = "kept"
    photo.review_note = "ok"
    photo.series_id = 2
    photo.series_rank = 1
    photo.selection_reason = "series_best"
    photo.manual_change = "manual_added"
    project = Project.new(tmp_path, [photo])
    project.snapshot.series = (SeriesGroup(2, (image,)),)
    project.snapshot.manual_corrections = [
        ManualCorrection(image, "manual_added", False, True, 2)
    ]
    return project


def test_new_project_defaults(tmp_path: Path) -> None:
    project = Project.new(tmp_path / "Festival", [Photo(tmp_path / "a.jpg")])

    assert project.name == "Festival"
    assert project.dirty is True
    assert project.snapshot.photos[0].path.name == "a.jpg"


def test_project_save_and_load_roundtrip(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    path = tmp_path / "Festival.b2project"

    ProjectStore().save(project, path)
    loaded = ProjectStore().load(path)
    photo = loaded.snapshot.photos[0]

    assert project_to_json(loaded)["project_format_version"] == PROJECT_FORMAT_VERSION
    assert photo.selected is True
    assert photo.favorite is True
    assert photo.tags == {"Bühne"}
    assert photo.rating == 4
    assert photo.ai_selected is True
    assert photo.ai_analysis is not None
    assert photo.review_status == "kept"
    assert loaded.snapshot.series[0].id == 2
    assert loaded.snapshot.manual_corrections[0].change_type == "manual_added"


def test_corrupt_project_file_raises_clean_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.b2project"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(ProjectFileError):
        ProjectStore().load(path)


def test_recovery_manager_detects_newer_autosave(tmp_path: Path) -> None:
    project_file = tmp_path / "Festival.b2project"
    autosave = tmp_path / "Festival.b2project.autosave"
    project_file.write_text("old", encoding="utf-8")
    autosave.write_text("new", encoding="utf-8")

    info = RecoveryManager().inspect(project_file)

    assert info.autosave_file == autosave
    assert info.has_recovery is True


def test_store_keeps_backup_on_second_save(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    path = tmp_path / "Festival.b2project"
    store = ProjectStore()

    store.save(project, path)
    project.mark_dirty()
    store.save(project)

    assert path.exists()
    assert (tmp_path / "Festival.b2project.bak").exists()
    assert not (tmp_path / "Festival.b2project.tmp").exists()


def test_missing_images_are_reported(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    path = tmp_path / "Festival.b2project"
    ProjectStore().save(project, path)
    project.snapshot.photos[0].path.unlink()

    loaded = ProjectStore().load(path)

    assert loaded.snapshot.missing_photos == (project.snapshot.photos[0].path,)


def test_recent_projects_skip_missing_files(tmp_path: Path) -> None:
    existing = tmp_path / "existing.b2project"
    missing = tmp_path / "missing.b2project"
    existing.write_text("{}", encoding="utf-8")
    recent = RecentProjects(tmp_path / "recent.json", limit=5)

    recent.add(missing)
    recent.add(existing)

    assert recent.list() == [existing.resolve()]


def test_dirty_state_and_autosave_without_timing(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    project = make_project(tmp_path)
    project.project_file = tmp_path / "Festival.b2project"
    store = ProjectStore()
    autosave = AutoSaveController(store, RecoveryManager(), debounce_ms=1, interval_ms=100000)
    autosave.set_project(project)

    autosave.mark_dirty()
    assert project.dirty is True
    assert autosave.save_if_dirty() is True

    assert (tmp_path / "Festival.b2project.autosave").exists()

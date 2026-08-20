from b2_photo_manager.services.export_presets import (
    ExportFormat,
    ExportPreset,
    FilenameMode,
    ResizeMode,
)
from b2_photo_manager.services.photo_exporter import ExportSummary
from b2_photo_manager.ui.main_window import (
    RECENT_PROJECT_LABEL_LIMIT,
    _compact_project_name,
    _export_history_entry,
)


def test_compact_project_name_keeps_short_names() -> None:
    assert _compact_project_name("Festival.b2project") == "Festival.b2project"


def test_compact_project_name_limits_long_recent_project_labels() -> None:
    name = "Ein extrem langer Projektname fuer einen sehr breiten Bildschirm.b2project"

    compact = _compact_project_name(name)

    assert len(compact) == RECENT_PROJECT_LABEL_LIMIT
    assert compact.startswith("Ein extrem")
    assert compact.endswith(".b2project")
    assert "..." in compact


def test_export_history_entry_stores_compact_summary(tmp_path) -> None:
    preset = ExportPreset(
        key="web",
        name="Website",
        output_format=ExportFormat.JPG,
        resize_mode=ResizeMode.BOUNDING_BOX,
        long_edge=None,
        max_width=1600,
        max_height=1200,
        quality=82,
        keep_metadata=False,
        filename_prefix="web",
        filename_mode=FilenameMode.PREFIX_NUMBER,
        start_number=1,
        number_padding=3,
    )
    summary = ExportSummary(destination_folder=tmp_path / "exports", results=())

    entry = _export_history_entry(summary, preset)

    assert entry["destination"] == str(tmp_path / "exports")
    assert entry["successful_count"] == 0
    assert entry["format"] == "jpg"
    assert entry["resize_mode"] == "bounding_box"
    assert entry["preset"] == "Website"


def test_load_photo_objects_keeps_thumbnail_workers_alive(tmp_path) -> None:
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication

    from b2_photo_manager.models.photo import Photo
    from b2_photo_manager.ui.main_window import MainWindow

    class ThreadPoolStub:
        def __init__(self) -> None:
            self.started = []

        def start(self, worker) -> None:
            self.started.append(worker)

    app = QApplication.instance() or QApplication([])
    photo_path = tmp_path / "bild.jpg"
    photo_path.write_bytes(b"not a real image")

    window = MainWindow()
    window.thread_pool = ThreadPoolStub()
    window._load_photo_objects([Photo(photo_path)], mark_dirty=False)
    app.processEvents()

    assert photo_path in window.thumbnail_workers
    assert window.thread_pool.started == [window.thumbnail_workers[photo_path]]

    window._on_thumbnail_loaded(photo_path, QImage(8, 8, QImage.Format.Format_RGB888), 1)

    assert photo_path not in window.thumbnail_workers
    window.close()

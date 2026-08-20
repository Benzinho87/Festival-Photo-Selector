from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QApplication

from b2_photo_manager import __version__
from b2_photo_manager.config import CONFIG
from b2_photo_manager.models.photo import Photo
from b2_photo_manager.resources import resource_path
from b2_photo_manager.runtime_paths import runtime_paths
from b2_photo_manager.services.project.model import Project
from b2_photo_manager.services.project.store import ProjectStore
from b2_photo_manager.ui.main_window import MainWindow

PYSIDE6_PLUGIN_GROUPS = (
    "platforms",
    "imageformats",
    "styles",
)


def pyinstaller_collect_args() -> tuple[str, ...]:
    return tuple(
        argument
        for group in PYSIDE6_PLUGIN_GROUPS
        for argument in ("--collect-submodules", f"PySide6.QtPlugins.{group}")
    )


def run_smoke_check() -> None:
    app = QApplication.instance() or QApplication([])
    paths = runtime_paths()
    paths.ensure()

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])).resolve()
    image_formats = sorted(
        bytes(fmt).decode("ascii") for fmt in QImageReader.supportedImageFormats()
    )
    checks = {
        "app_name": CONFIG.app_name,
        "version": __version__,
        "qt_platform": app.platformName(),
        "image_formats": image_formats,
        "resource_probe": str(resource_path("placeholder.txt")),
        "bundle_root": str(bundle_root),
        "app_support": str(paths.app_support),
        "cache": str(paths.cache),
        "logs": str(paths.logs),
    }

    if sys.platform == "darwin" and checks["qt_platform"] != "cocoa":
        raise RuntimeError(f"Expected Qt platform cocoa, got {checks['qt_platform']}")
    for key in ("app_support", "cache", "logs"):
        path = Path(checks[key]).resolve()
        if bundle_root in path.parents or path == bundle_root:
            raise RuntimeError(f"{key} points inside the app bundle: {path}")

    source_dir = paths.app_support / "packaging-smoke-source"
    source_dir.mkdir(parents=True, exist_ok=True)
    photo_path = source_dir / "smoke.jpg"
    photo_path.write_bytes(b"smoke")
    project_path = paths.app_support / "packaging-smoke.b2project"
    project = Project.new(source_dir, [Photo(photo_path, selected=True)])
    store = ProjectStore()
    store.save(project, project_path)
    loaded = store.load(project_path)
    if loaded.name != source_dir.name or len(loaded.snapshot.photos) != 1:
        raise RuntimeError("Project smoke check failed")

    window = MainWindow()
    window.resize(900, 600)
    window.show()
    app.processEvents()
    checks["ui_loaded"] = window.windowTitle()
    window.close()

    print(json.dumps(checks, indent=2, sort_keys=True))

import os
from pathlib import Path

import pytest

from b2_photo_manager.cli import main
from b2_photo_manager.packaging import PYSIDE6_PLUGIN_GROUPS
from b2_photo_manager.resources import resource_path
from b2_photo_manager.runtime_paths import runtime_paths


def test_main_entrypoint_is_central_callable() -> None:
    assert callable(main)


def test_runtime_paths_are_not_relative_to_cwd(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    paths = runtime_paths(Path("/Users/example"), "Darwin")

    assert paths.app_support.is_absolute()
    assert paths.cache.is_absolute()
    assert paths.logs.is_absolute()
    assert tmp_path not in paths.app_support.parents
    assert tmp_path not in paths.cache.parents
    assert tmp_path not in paths.logs.parents


def test_resource_path_rejects_unsafe_names() -> None:
    with pytest.raises(ValueError):
        resource_path("../secret.txt")
    with pytest.raises(ValueError):
        resource_path("/tmp/secret.txt")


def test_resource_path_supports_pyinstaller_bundle(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False)

    assert resource_path("icon.icns") == tmp_path / "b2_photo_manager" / "assets" / "icon.icns"


def test_no_manual_qt_plugin_path_is_configured() -> None:
    assert "QT_PLUGIN_PATH" not in os.environ
    assert "QT_QPA_PLATFORM_PLUGIN_PATH" not in os.environ


def test_pyinstaller_plugin_groups_include_macos_platform_and_images() -> None:
    assert "platforms" in PYSIDE6_PLUGIN_GROUPS
    assert "imageformats" in PYSIDE6_PLUGIN_GROUPS

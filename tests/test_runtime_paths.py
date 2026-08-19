from pathlib import Path

from b2_photo_manager.runtime_paths import APP_DIR_NAME, runtime_paths


def test_runtime_paths_use_macos_library_locations() -> None:
    paths = runtime_paths(Path("/Users/example"), "Darwin")

    assert paths.app_support == Path("/Users/example/Library/Application Support") / APP_DIR_NAME
    assert paths.cache == Path("/Users/example/Library/Caches") / APP_DIR_NAME
    assert paths.logs == Path("/Users/example/Library/Logs") / APP_DIR_NAME
    assert paths.recent_projects_file == paths.app_support / "recent-projects.json"
    assert paths.ai_cache_dir == paths.cache / "ai"


def test_runtime_paths_have_linux_fallback() -> None:
    paths = runtime_paths(Path("/home/example"), "Linux")

    assert paths.app_support == Path("/home/example/.local/share") / APP_DIR_NAME
    assert paths.cache == Path("/home/example/.cache") / APP_DIR_NAME
    assert paths.logs == Path("/home/example/.local/state") / APP_DIR_NAME / "logs"

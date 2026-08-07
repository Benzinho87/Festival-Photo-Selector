import os
import sys
from pathlib import Path


def prepare_runtime() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            "B² Photo Manager benötigt Python 3.12. "
            f"Aktiv ist Python {sys.version_info.major}.{sys.version_info.minor}."
        )

    _configure_qt_platform_plugin()


def _configure_qt_platform_plugin() -> None:
    if sys.platform != "darwin":
        return

    try:
        import PySide6
    except ImportError:
        return

    pyside_root = Path(PySide6.__file__).resolve().parent
    candidates = [
        pyside_root / "Qt" / "plugins" / "platforms",
        pyside_root / "plugins" / "platforms",
    ]

    for plugin_dir in candidates:
        cocoa_plugin = plugin_dir / "libqcocoa.dylib"
        if cocoa_plugin.exists():
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugin_dir)
            return

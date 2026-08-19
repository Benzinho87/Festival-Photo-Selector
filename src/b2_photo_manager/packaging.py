from __future__ import annotations

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

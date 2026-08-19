from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path

RESOURCE_PACKAGE = "b2_photo_manager.assets"


def resource_path(name: str) -> Path:
    if not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("resource name must be a package-relative path")
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root) / "b2_photo_manager" / "assets" / name
    return Path(str(resources.files(RESOURCE_PACKAGE).joinpath(name)))

from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def find_photos(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise NotADirectoryError(folder)

    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

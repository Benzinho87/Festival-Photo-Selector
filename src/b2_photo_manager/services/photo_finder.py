from pathlib import Path
SUPPORTED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})

def find_photos(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    return sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Photo:
    path: Path
    selected: bool = False
    rating: int = 0
    photographer: str | None = None

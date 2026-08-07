from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Photo:
    path: Path
    selected: bool = False
    rating: int = 0
    photographer: str | None = None

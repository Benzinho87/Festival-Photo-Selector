from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Photo:
    path: Path
    selected: bool = False
    favorite: bool = False
    tags: set[str] = field(default_factory=set)
    rating: int = 0
    photographer: str | None = None

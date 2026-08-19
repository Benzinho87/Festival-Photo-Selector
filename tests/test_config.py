import tomllib
from pathlib import Path

from b2_photo_manager import __version__
from b2_photo_manager.config import CONFIG


def test_config_version() -> None:
    assert CONFIG.version == "0.6.3"
    assert CONFIG.version == __version__
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == CONFIG.version

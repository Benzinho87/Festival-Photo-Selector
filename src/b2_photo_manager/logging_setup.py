import logging
from pathlib import Path

from b2_photo_manager.config import CONFIG


def setup_logging() -> None:
    log_directory = Path(CONFIG.log_directory)
    log_directory.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(
                log_directory / "b2-photo-manager.log",
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )

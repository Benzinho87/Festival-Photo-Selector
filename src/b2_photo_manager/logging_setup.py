import logging
from b2_photo_manager.config import CONFIG

def configure_logging() -> None:
    CONFIG.log_directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(CONFIG.log_directory / "b2-photo-manager.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

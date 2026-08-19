import logging
import platform
import sys
from logging.handlers import RotatingFileHandler

import PySide6

from b2_photo_manager import __version__
from b2_photo_manager.config import CONFIG
from b2_photo_manager.runtime_paths import runtime_paths


def setup_logging() -> None:
    paths = runtime_paths()
    paths.ensure()

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if root.handlers:
        return
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = RotatingFileHandler(
        paths.log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    logging.getLogger(__name__).info(
        "%s gestartet | Version %s | Python %s | PySide6 %s | %s",
        CONFIG.app_name,
        __version__,
        sys.version.split()[0],
        PySide6.__version__,
        platform.platform(),
    )


def log_runtime_paths() -> None:
    paths = runtime_paths()
    logging.getLogger(__name__).info(
        "Runtime-Pfade | App Support: %s | Cache: %s | Logs: %s",
        paths.app_support,
        paths.cache,
        paths.logs,
    )

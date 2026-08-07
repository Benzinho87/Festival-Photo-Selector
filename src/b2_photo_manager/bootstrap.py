import sys


def prepare_runtime() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            "B² Photo Manager benötigt Python 3.12. "
            f"Aktiv ist Python {sys.version_info.major}.{sys.version_info.minor}."
        )
